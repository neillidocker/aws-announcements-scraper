"""
Content extractor module for parsing announcement pages.

This module provides functionality to extract structured content from
AWS announcement pages including title, publication date, content text,
and embedded links.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from .http_client import HTTPClient
from .models import AnnouncementContent, EmbeddedLink

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Extracts structured content from AWS announcement pages."""
    
    def __init__(self, http_client: HTTPClient):
        """
        Initialize content extractor with HTTP client.
        
        Args:
            http_client: HTTP client for fetching pages
        """
        self.http_client = http_client
        logger.info("ContentExtractor initialized")
    
    def extract_content(self, url: str, publication_date: Optional[datetime] = None) -> AnnouncementContent:
        """
        Extract complete content from an announcement page.
        
        Args:
            url: URL of the announcement page to extract
            publication_date: Optional publication date from homepage data
            
        Returns:
            AnnouncementContent object with extracted data
            
        Raises:
            requests.RequestException: For network or HTTP errors
            ValueError: For parsing errors or missing required content
        """
        logger.info(f"Extracting content from: {url}")
        
        try:
            # Fetch the page content
            response = self.http_client.fetch_with_retry(url)
            html_content = response.text
            
            # Parse the content
            announcement_content = self.parse_announcement_page(html_content, url, publication_date)
            
            logger.info(f"Successfully extracted content from {url}")
            return announcement_content
            
        except requests.RequestException as e:
            logger.error(f"Failed to fetch content from {url}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse content from {url}: {str(e)}")
            raise ValueError(f"Content parsing failed: {str(e)}")
    
    def parse_announcement_page(self, html_content: str, url: str, publication_date: Optional[datetime] = None) -> AnnouncementContent:
        """
        Parse HTML content to extract structured announcement data.
        
        Args:
            html_content: Raw HTML content of the page
            url: Source URL for reference
            publication_date: Optional publication date from homepage data
            
        Returns:
            AnnouncementContent object with extracted data
            
        Raises:
            ValueError: If required content cannot be extracted
        """
        logger.debug(f"Parsing announcement page content for {url}")
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract title
        title = self._extract_title(soup)
        if not title:
            raise ValueError("Could not extract title from announcement page")
        
        # Use provided publication date or try to extract from page
        if publication_date:
            logger.debug(f"Using provided publication date: {publication_date}")
        else:
            publication_date = self._extract_publication_date(soup)
            if not publication_date:
                logger.warning(f"Could not extract publication date from {url}, using current time")
                publication_date = datetime.now()
        
        # Extract main content text
        content_text = self._extract_content_text(soup)
        if not content_text:
            raise ValueError("Could not extract content text from announcement page")
        
        # Extract embedded links
        embedded_links = self.extract_embedded_links(soup, url)
        
        # Create the announcement content object
        announcement_content = AnnouncementContent(
            title=title,
            url=url,
            publication_date=publication_date,
            content_text=content_text,
            embedded_links=embedded_links,
            extraction_timestamp=datetime.now()
        )
        
        logger.debug(f"Parsed announcement: title='{title}', links={len(embedded_links)}")
        return announcement_content
    
    def extract_embedded_links(self, soup: BeautifulSoup, base_url: str) -> List[EmbeddedLink]:
        """
        Extract all embedded links from the announcement content.
        
        Args:
            soup: BeautifulSoup object of the parsed HTML
            base_url: Base URL for resolving relative links
            
        Returns:
            List of EmbeddedLink objects
        """
        logger.debug("Extracting embedded links from content")
        
        embedded_links = []
        
        # Find the main content area (try multiple selectors)
        content_area = self._find_content_area(soup)
        if not content_area:
            logger.warning("Could not identify main content area, searching entire document")
            content_area = soup
        
        # Find all links within the content area
        links = content_area.find_all('a', href=True)
        
        for link in links:
            try:
                href = link.get('href', '').strip()
                if not href:
                    continue
                
                # Resolve relative URLs
                absolute_url = urljoin(base_url, href)
                
                # Skip internal page anchors
                if href.startswith('#'):
                    continue
                
                # Get link text
                link_text = link.get_text(strip=True)
                if not link_text:
                    link_text = href  # Use URL as fallback
                
                # Get surrounding context (parent element text)
                context = self._get_link_context(link)
                
                embedded_link = EmbeddedLink(
                    text=link_text,
                    url=absolute_url,
                    context=context
                )
                
                embedded_links.append(embedded_link)
                logger.debug(f"Found embedded link: {link_text} -> {absolute_url}")
                
            except Exception as e:
                logger.warning(f"Failed to process embedded link: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(embedded_links)} embedded links")
        return embedded_links
    
    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the title from the announcement page."""
        # Try multiple selectors for title
        title_selectors = [
            'h1',
            '.announcement-title',
            '.post-title',
            '.article-title',
            'title'
        ]
        
        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if title and len(title) > 5:  # Basic validation
                    logger.debug(f"Found title using selector '{selector}': {title}")
                    return title
        
        logger.warning("Could not extract title using any selector")
        return None
    
    def _extract_publication_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract the publication date from the announcement page."""
        # Try multiple approaches to find publication date
        
        # 1. Look for structured data (JSON-LD, microdata)
        date = self._extract_structured_date(soup)
        if date:
            return date
        
        # 2. Look for common date selectors
        date_selectors = [
            '.publication-date',
            '.post-date',
            '.article-date',
            '.date',
            'time[datetime]',
            '.published'
        ]
        
        for selector in date_selectors:
            date_element = soup.select_one(selector)
            if date_element:
                date = self._parse_date_from_element(date_element)
                if date:
                    logger.debug(f"Found date using selector '{selector}': {date}")
                    return date
        
        # 3. Search for date patterns in text
        date = self._extract_date_from_text(soup)
        if date:
            return date
        
        logger.warning("Could not extract publication date")
        return None
    
    def _extract_content_text(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract the main content text from the announcement page."""
        # Find the main content area
        content_area = self._find_content_area(soup)
        
        if content_area:
            # Extract text while preserving some formatting
            content_text = self._extract_formatted_text(content_area)
            if content_text and len(content_text.strip()) > 50:  # Basic validation
                logger.debug(f"Extracted content text: {len(content_text)} characters")
                return content_text
        
        logger.warning("Could not extract content text")
        return None
    
    def _find_content_area(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find the main content area of the announcement page."""
        # Try multiple selectors for main content
        content_selectors = [
            'article',
            '.announcement-content',
            '.post-content',
            '.article-content',
            '.content',
            'main',
            '#content',
            '.main-content'
        ]
        
        for selector in content_selectors:
            content_area = soup.select_one(selector)
            if content_area:
                logger.debug(f"Found content area using selector: {selector}")
                return content_area
        
        # Fallback: look for the largest text block
        return self._find_largest_text_block(soup)
    
    def _find_largest_text_block(self, soup: BeautifulSoup) -> Optional[Tag]:
        """Find the element with the most text content as fallback."""
        candidates = soup.find_all(['div', 'section', 'article'])
        
        best_candidate = None
        max_text_length = 0
        
        for candidate in candidates:
            text_length = len(candidate.get_text(strip=True))
            if text_length > max_text_length:
                max_text_length = text_length
                best_candidate = candidate
        
        if best_candidate and max_text_length > 100:
            logger.debug(f"Found largest text block with {max_text_length} characters")
            return best_candidate
        
        return None
    
    def _extract_formatted_text(self, element: Tag) -> str:
        """Extract text while preserving basic formatting."""
        # Remove script and style elements
        for script in element(["script", "style"]):
            script.decompose()
        
        # Get text with some formatting preservation
        text_parts = []
        
        for child in element.descendants:
            if child.name in ['p', 'div', 'br']:
                text_parts.append('\n')
            elif child.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                text_parts.append('\n\n')
            elif isinstance(child, str):
                text_parts.append(child)
        
        # Clean up the text
        text = ''.join(text_parts)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Remove excessive newlines
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize whitespace
        
        return text.strip()
    
    def _extract_structured_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract date from structured data (JSON-LD, microdata)."""
        # Look for JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                
                # Look for datePublished or dateCreated
                date_fields = ['datePublished', 'dateCreated', 'dateModified']
                for field in date_fields:
                    if field in data:
                        date_str = data[field]
                        date = self._parse_date_string(date_str)
                        if date:
                            logger.debug(f"Found date in JSON-LD {field}: {date}")
                            return date
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Look for microdata
        time_elements = soup.find_all('time', {'datetime': True})
        for time_elem in time_elements:
            date_str = time_elem.get('datetime')
            date = self._parse_date_string(date_str)
            if date:
                logger.debug(f"Found date in time element: {date}")
                return date
        
        return None
    
    def _parse_date_from_element(self, element: Tag) -> Optional[datetime]:
        """Parse date from a DOM element."""
        # Try datetime attribute first
        datetime_attr = element.get('datetime')
        if datetime_attr:
            date = self._parse_date_string(datetime_attr)
            if date:
                return date
        
        # Try element text
        text = element.get_text(strip=True)
        return self._parse_date_string(text)
    
    def _extract_date_from_text(self, soup: BeautifulSoup) -> Optional[datetime]:
        """Extract date from text patterns in the page."""
        text = soup.get_text()
        
        # Common date patterns
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{2}/\d{2}/\d{4})',  # MM/DD/YYYY
            r'(\d{2}-\d{2}-\d{4})',  # MM-DD-YYYY
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}',  # Month DD, YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                date = self._parse_date_string(match)
                if date:
                    logger.debug(f"Found date in text using pattern: {date}")
                    return date
        
        return None
    
    def _parse_date_string(self, date_str: str) -> Optional[datetime]:
        """Parse a date string using multiple formats."""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Common date formats to try
        date_formats = [
            '%Y-%m-%d',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
            '%Y-%m-%dT%H:%M:%S.%fZ',
            '%m/%d/%Y',
            '%m-%d-%Y',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y'
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        logger.debug(f"Could not parse date string: {date_str}")
        return None
    
    def _get_link_context(self, link: Tag) -> str:
        """Get surrounding context text for a link."""
        # Get parent element text, but limit to reasonable length
        parent = link.parent
        if parent:
            context_text = parent.get_text(strip=True)
            # Limit context length and clean up
            if len(context_text) > 200:
                context_text = context_text[:200] + "..."
            return context_text
        
        return ""