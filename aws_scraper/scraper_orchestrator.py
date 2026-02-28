"""
Main scraper orchestrator for coordinating the scraping workflow.

This module provides the main ScraperOrchestrator class that coordinates
all components to perform the complete scraping workflow.
"""

import logging
import time
from datetime import datetime
from typing import List, Optional

from .config_manager import ConfigurationManager
from .http_client import HTTPClient
from .homepage_parser import HomepageParser
from .content_extractor import ContentExtractor
from .date_filter import DateFilter
from .data_storage import DataStorage
from .models import ScrapingResult, AnnouncementContent, FailedExtraction, AnnouncementLink

logger = logging.getLogger(__name__)


class ScraperOrchestrator:
    """Main orchestrator class for coordinating the scraping workflow."""
    
    def __init__(self, config_manager: Optional[ConfigurationManager] = None):
        """
        Initialize the scraper orchestrator with configuration.
        
        Args:
            config_manager: Configuration manager instance, creates default if None
        """
        self.config_manager = config_manager or ConfigurationManager()
        
        # Initialize components
        self.http_client = HTTPClient(
            timeout=self.config_manager.get('http.timeout', 30)
        )
        self.homepage_parser = HomepageParser()
        self.content_extractor = ContentExtractor(self.http_client)
        self.date_filter = DateFilter()
        self.data_storage = DataStorage(self.config_manager.config)
        
        # Progress tracking
        self.total_links_found = 0
        self.successful_extractions = 0
        self.failed_extractions = 0
        
        logger.info("ScraperOrchestrator initialized with all components")
    
    def run_scraping_workflow(self, target_url: Optional[str] = None) -> ScrapingResult:
        """
        Run the complete scraping workflow.
        
        Args:
            target_url: URL of the AWS homepage to scrape (if None, uses language-specific URL from config)
            
        Returns:
            ScrapingResult containing all extraction results and metadata
        """
        # Determine target URL based on language setting if not provided
        if target_url is None:
            language = self.config_manager.get('scraping.language', 'en')
            target_url = self.config_manager.get(f'scraping.base_urls.{language}')
            if not target_url:
                # Fallback to default English URL
                target_url = "https://www.amazonaws.cn/en/new/"
                logger.warning(f"No URL configured for language '{language}', using default: {target_url}")
        
        start_time = time.time()
        successful_extractions: List[AnnouncementContent] = []
        failed_extractions: List[FailedExtraction] = []
        
        language = self.config_manager.get('scraping.language', 'en')
        language_name = "English" if language == 'en' else "Chinese"
        
        logger.info("Starting AWS announcements scraping workflow")
        logger.info(f"Language: {language_name} ({language})")
        logger.info(f"Target URL: {target_url}")
        
        try:
            # Step 1: Fetch and parse homepage
            logger.info("Step 1: Fetching and parsing homepage")
            announcement_links = self._fetch_homepage_links(target_url)
            
            if not announcement_links:
                logger.warning("No announcement links found on homepage")
                return self._create_result([], [], 0, time.time() - start_time)
            
            self.total_links_found = len(announcement_links)
            logger.info(f"Found {self.total_links_found} announcement links")
            
            # Step 2: Apply date filtering to links BEFORE content extraction
            logger.info("Step 2: Applying date filtering to announcement links")
            filtered_links = self._apply_date_filtering_to_links(announcement_links)
            
            # Step 3: Extract content only from filtered announcements
            logger.info("Step 3: Extracting content from filtered announcements")
            successful_extractions, failed_extractions = self._extract_all_content(filtered_links)
            
            # No need for additional filtering since we already filtered the links
            filtered_extractions = successful_extractions
            
            # Step 4: Store results
            logger.info("Step 4: Storing results")
            result = self._create_result(filtered_extractions, failed_extractions, 
                                       self.total_links_found, time.time() - start_time)
            
            # Store the data
            output_path = self.data_storage.store_data(result)
            logger.info(f"Results stored to: {output_path}")
            
            # Log final summary
            self._log_final_summary(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Scraping workflow failed: {str(e)}")
            # Create a failure result
            failure = FailedExtraction(
                url=target_url,
                error_message=str(e),
                error_type=type(e).__name__,
                timestamp=datetime.now()
            )
            return self._create_result([], [failure], 0, time.time() - start_time)
    
    def _fetch_homepage_links(self, target_url: str) -> List[AnnouncementLink]:
        """
        Fetch and parse homepage to extract announcement links.
        
        Args:
            target_url: URL of the homepage to fetch
            
        Returns:
            List of announcement links found
            
        Raises:
            Exception: If homepage fetching or parsing fails
        """
        try:
            logger.info(f"Fetching homepage: {target_url}")
            response = self.http_client.fetch_with_retry(
                target_url, 
                max_retries=self.config_manager.get('http.max_retries', 3)
            )
            
            logger.info("Parsing homepage for announcement links")
            announcement_links = self.homepage_parser.parse_homepage(response.text)
            
            logger.info(f"Successfully extracted {len(announcement_links)} links from homepage")
            return announcement_links
            
        except Exception as e:
            logger.error(f"Failed to fetch or parse homepage: {str(e)}")
            raise
    
    def _extract_all_content(self, announcement_links: List[AnnouncementLink]) -> tuple[List[AnnouncementContent], List[FailedExtraction]]:
        """
        Extract content from all announcement links with progress tracking.
        
        Args:
            announcement_links: List of announcement links to process
            
        Returns:
            Tuple of (successful_extractions, failed_extractions)
        """
        successful_extractions: List[AnnouncementContent] = []
        failed_extractions: List[FailedExtraction] = []
        
        rate_limit_delay = self.config_manager.get('http.rate_limit_delay', 1.0)
        
        for i, link in enumerate(announcement_links, 1):
            logger.info(f"Processing announcement {i}/{len(announcement_links)}: {link.title}")
            
            try:
                # Extract content from the announcement page
                content = self.content_extractor.extract_content(link.url, link.publication_date)
                successful_extractions.append(content)
                self.successful_extractions += 1
                
                logger.info(f"Successfully extracted content from: {link.url}")
                
            except Exception as e:
                # Record the failure and continue
                failure = FailedExtraction(
                    url=link.url,
                    error_message=str(e),
                    error_type=type(e).__name__,
                    timestamp=datetime.now()
                )
                failed_extractions.append(failure)
                self.failed_extractions += 1
                
                logger.error(f"Failed to extract content from {link.url}: {str(e)}")
            
            # Rate limiting: add delay between requests
            if i < len(announcement_links) and rate_limit_delay > 0:
                logger.debug(f"Rate limiting: waiting {rate_limit_delay}s before next request")
                time.sleep(rate_limit_delay)
            
            # Progress update every 10 items
            if i % 10 == 0 or i == len(announcement_links):
                self._log_progress_update(i, len(announcement_links))
        
        logger.info(f"Content extraction complete: {len(successful_extractions)} successful, {len(failed_extractions)} failed")
        return successful_extractions, failed_extractions
    
    def _apply_date_filtering_to_links(self, announcement_links: List[AnnouncementLink]) -> List[AnnouncementLink]:
        """
        Apply date filtering to announcement links BEFORE content extraction.
        
        Args:
            announcement_links: List of announcement links to filter
            
        Returns:
            Filtered list of announcement links
        """
        date_filter_config = self.config_manager.get('filtering.date_filter')
        
        if not date_filter_config:
            logger.info("No date filter configured, returning all announcement links")
            return announcement_links
        
        logger.info(f"Applying date filter to links: {date_filter_config}")
        
        try:
            # Parse the date filter (YYYY-MM format)
            year_str, month_str = date_filter_config.split('-')
            filter_year = int(year_str)
            filter_month = int(month_str)
            
            filtered_links = []
            
            for link in announcement_links:
                if link.publication_date:
                    # Check if the publication date matches the filter
                    if (link.publication_date.year == filter_year and 
                        link.publication_date.month == filter_month):
                        filtered_links.append(link)
                        logger.debug(f"Link matches filter: {link.title} ({link.publication_date.strftime('%Y-%m-%d')})")
                    else:
                        logger.debug(f"Link filtered out: {link.title} ({link.publication_date.strftime('%Y-%m-%d')})")
                else:
                    # If no publication date, skip this link when filtering
                    logger.debug(f"Link has no publication date, skipping: {link.title}")
            
            logger.info(f"Date filtering complete: {len(filtered_links)}/{len(announcement_links)} links match filter")
            return filtered_links
            
        except Exception as e:
            logger.error(f"Date filtering failed: {str(e)}")
            logger.info("Returning unfiltered announcement links")
            return announcement_links
    
    def _apply_date_filtering(self, announcements: List[AnnouncementContent]) -> List[AnnouncementContent]:
        """
        Apply date filtering to announcements if configured.
        
        Args:
            announcements: List of announcements to filter
            
        Returns:
            Filtered list of announcements
        """
        date_filter_config = self.config_manager.get('filtering.date_filter')
        
        if not date_filter_config:
            logger.info("No date filter configured, returning all announcements")
            return announcements
        
        logger.info(f"Applying date filter: {date_filter_config}")
        
        try:
            filtered_announcements = self.date_filter.filter_by_date(announcements, date_filter_config)
            logger.info(f"Date filtering complete: {len(filtered_announcements)}/{len(announcements)} announcements match filter")
            return filtered_announcements
            
        except Exception as e:
            logger.error(f"Date filtering failed: {str(e)}")
            logger.info("Returning unfiltered announcements")
            return announcements
    
    def _create_result(self, successful_extractions: List[AnnouncementContent], 
                      failed_extractions: List[FailedExtraction],
                      total_processed: int, execution_time: float) -> ScrapingResult:
        """
        Create a ScrapingResult object with all the collected data.
        
        Args:
            successful_extractions: List of successfully extracted announcements
            failed_extractions: List of failed extraction attempts
            total_processed: Total number of links processed
            execution_time: Total execution time in seconds
            
        Returns:
            ScrapingResult object
        """
        return ScrapingResult(
            successful_extractions=successful_extractions,
            failed_extractions=failed_extractions,
            total_processed=total_processed,
            execution_time=execution_time
        )
    
    def _log_progress_update(self, current: int, total: int) -> None:
        """
        Log progress update with current statistics.
        
        Args:
            current: Current item number being processed
            total: Total number of items to process
        """
        percentage = (current / total) * 100
        logger.info(f"Progress: {current}/{total} ({percentage:.1f}%) - "
                   f"Success: {self.successful_extractions}, Failed: {self.failed_extractions}")
    
    def _log_final_summary(self, result: ScrapingResult) -> None:
        """
        Log comprehensive final summary of the scraping operation.
        
        Args:
            result: The final scraping result
        """
        logger.info("=" * 60)
        logger.info("SCRAPING WORKFLOW COMPLETED")
        logger.info("=" * 60)
        logger.info(f"Total links found: {self.total_links_found}")
        logger.info(f"Total processed: {result.total_processed}")
        logger.info(f"Successful extractions: {len(result.successful_extractions)}")
        logger.info(f"Failed extractions: {len(result.failed_extractions)}")
        logger.info(f"Success rate: {(len(result.successful_extractions) / max(result.total_processed, 1)) * 100:.1f}%")
        logger.info(f"Execution time: {result.execution_time:.2f} seconds")
        
        # Log date filtering info if applied
        date_filter_config = self.config_manager.get('filtering.date_filter')
        if date_filter_config:
            logger.info(f"Date filter applied: {date_filter_config}")
        
        # Log language info
        language = self.config_manager.get('scraping.language', 'en')
        language_name = "English" if language == 'en' else "Chinese"
        logger.info(f"Language: {language_name} ({language})")
        
        # Log output configuration
        output_format = self.config_manager.get('output.format', 'json')
        output_dir = self.config_manager.get('output.directory', './output')
        logger.info(f"Output format: {output_format}")
        logger.info(f"Output directory: {output_dir}")
        
        # Log any failures for review
        if result.failed_extractions:
            logger.warning("Failed extractions:")
            for failure in result.failed_extractions[:5]:  # Show first 5 failures
                logger.warning(f"  - {failure.url}: {failure.error_type} - {failure.error_message}")
            if len(result.failed_extractions) > 5:
                logger.warning(f"  ... and {len(result.failed_extractions) - 5} more failures")
        
        logger.info("=" * 60)