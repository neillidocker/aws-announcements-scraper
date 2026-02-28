"""
Data storage module for managing scraping results.

This module handles storage and output of scraping results in multiple
formats including JSON, CSV, and plain text.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from .models import ScrapingResult, AnnouncementContent, FailedExtraction

logger = logging.getLogger(__name__)


class DataStorage:
    """Manages storage and output of scraping results with duplicate handling."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize DataStorage with configuration settings."""
        self.config = config
        self.output_format = config.get('output', {}).get('format', 'json')
        self.output_directory = Path(config.get('output', {}).get('directory', './output'))
        self.filename_template = config.get('output', {}).get('filename_template', 'aws_announcements_{timestamp}')
        self.include_metadata = config.get('output', {}).get('include_metadata', True)
        self.duplicate_handling = config.get('filtering', {}).get('duplicate_handling', 'skip')
        
        # Ensure output directory exists
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Track stored data for duplicate detection
        self._stored_urls: set = set()
        self._stored_data: List[AnnouncementContent] = []
    
    def store_data(self, scraping_result: ScrapingResult) -> str:
        """
        Store scraping results with metadata inclusion and duplicate handling.
        
        Args:
            scraping_result: The complete scraping result to store
            
        Returns:
            str: Path to the output file
        """
        logger.info(f"Storing {len(scraping_result.successful_extractions)} successful extractions")
        
        # Handle duplicates
        filtered_data = self._handle_duplicates(scraping_result.successful_extractions)
        
        # Create output data structure
        output_data = self._prepare_output_data(filtered_data, scraping_result)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.filename_template.format(timestamp=timestamp)
        
        # Store in the specified format
        if self.output_format == 'json':
            output_path = self._store_json(output_data, filename)
        elif self.output_format == 'csv':
            output_path = self._store_csv(filtered_data, scraping_result, filename)
        elif self.output_format == 'txt':
            output_path = self._store_text(filtered_data, scraping_result, filename)
        elif self.output_format == 'html':
            output_path = self._store_html(filtered_data, scraping_result, filename)
        else:
            raise ValueError(f"Unsupported output format: {self.output_format}")
        
        logger.info(f"Data stored successfully to {output_path}")
        return str(output_path)
    
    def _handle_duplicates(self, announcements: List[AnnouncementContent]) -> List[AnnouncementContent]:
        """Handle duplicate announcements based on configuration."""
        if self.duplicate_handling == 'skip':
            # Skip announcements with URLs we've already seen
            filtered = []
            for announcement in announcements:
                if announcement.url not in self._stored_urls:
                    filtered.append(announcement)
                    self._stored_urls.add(announcement.url)
                else:
                    logger.debug(f"Skipping duplicate URL: {announcement.url}")
            return filtered
        
        elif self.duplicate_handling == 'overwrite':
            # Always include all announcements, overwriting previous versions
            for announcement in announcements:
                self._stored_urls.add(announcement.url)
            return announcements
        
        elif self.duplicate_handling == 'version':
            # Create versioned entries for duplicates
            versioned = []
            url_counts = {}
            
            for announcement in announcements:
                if announcement.url in url_counts:
                    url_counts[announcement.url] += 1
                    version = url_counts[announcement.url]
                    # Create a versioned copy
                    versioned_announcement = AnnouncementContent(
                        title=f"{announcement.title} (v{version})",
                        url=announcement.url,
                        publication_date=announcement.publication_date,
                        content_text=announcement.content_text,
                        embedded_links=announcement.embedded_links,
                        extraction_timestamp=announcement.extraction_timestamp
                    )
                    versioned.append(versioned_announcement)
                else:
                    url_counts[announcement.url] = 1
                    versioned.append(announcement)
                
                self._stored_urls.add(announcement.url)
            
            return versioned
        
        else:
            logger.warning(f"Unknown duplicate handling strategy: {self.duplicate_handling}, using 'skip'")
            return self._handle_duplicates(announcements)
    
    def _prepare_output_data(self, announcements: List[AnnouncementContent], 
                           scraping_result: ScrapingResult) -> Dict[str, Any]:
        """Prepare structured output data with metadata."""
        output_data = {
            "announcements": [self._announcement_to_dict(ann) for ann in announcements],
            "summary": {
                "total_processed": scraping_result.total_processed,
                "successful_extractions": len(announcements),
                "failed_extractions": len(scraping_result.failed_extractions),
                "execution_time": scraping_result.execution_time
            }
        }
        
        if self.include_metadata:
            output_data["metadata"] = {
                "extraction_timestamp": datetime.now().isoformat(),
                "scraper_version": "1.0.0",
                "output_format": self.output_format,
                "duplicate_handling": self.duplicate_handling,
                "configuration": {
                    "timeout": self.config.get('http', {}).get('timeout'),
                    "max_retries": self.config.get('http', {}).get('max_retries'),
                    "date_filter": self.config.get('filtering', {}).get('date_filter')
                }
            }
            
            # Include failed extractions if any
            if scraping_result.failed_extractions:
                output_data["failed_extractions"] = [
                    {
                        "url": failure.url,
                        "error_message": failure.error_message,
                        "error_type": failure.error_type,
                        "timestamp": failure.timestamp.isoformat()
                    }
                    for failure in scraping_result.failed_extractions
                ]
        
        return output_data
    
    def _announcement_to_dict(self, announcement: AnnouncementContent) -> Dict[str, Any]:
        """Convert AnnouncementContent to dictionary format."""
        return {
            "title": announcement.title,
            "url": announcement.url,
            "publication_date": announcement.publication_date.isoformat(),
            "content_text": announcement.content_text,
            "embedded_links": [
                {
                    "text": link.text,
                    "url": link.url,
                    "context": link.context
                }
                for link in announcement.embedded_links
            ],
            "extraction_timestamp": announcement.extraction_timestamp.isoformat()
        }
    
    def _store_json(self, output_data: Dict[str, Any], filename: str) -> Path:
        """Store data in JSON format."""
        output_path = self.output_directory / f"{filename}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def _store_csv(self, announcements: List[AnnouncementContent], 
                   scraping_result: ScrapingResult, filename: str) -> Path:
        """Store data in CSV format."""
        output_path = self.output_directory / f"{filename}.csv"
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Write header
            headers = ['title', 'url', 'publication_date', 'content_text', 'embedded_links_count', 'extraction_timestamp']
            if self.include_metadata:
                headers.extend(['total_processed', 'execution_time'])
            writer.writerow(headers)
            
            # Write announcement data
            for announcement in announcements:
                row = [
                    announcement.title,
                    announcement.url,
                    announcement.publication_date.isoformat(),
                    announcement.content_text,
                    len(announcement.embedded_links),
                    announcement.extraction_timestamp.isoformat()
                ]
                
                if self.include_metadata:
                    row.extend([scraping_result.total_processed, scraping_result.execution_time])
                
                writer.writerow(row)
        
        return output_path
    
    def _store_text(self, announcements: List[AnnouncementContent], 
                    scraping_result: ScrapingResult, filename: str) -> Path:
        """Store data in plain text format."""
        output_path = self.output_directory / f"{filename}.txt"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write header with metadata if enabled
            if self.include_metadata:
                f.write("AWS Announcements Scraping Results\n")
                f.write("=" * 40 + "\n\n")
                f.write(f"Extraction Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Processed: {scraping_result.total_processed}\n")
                f.write(f"Successful Extractions: {len(announcements)}\n")
                f.write(f"Failed Extractions: {len(scraping_result.failed_extractions)}\n")
                f.write(f"Execution Time: {scraping_result.execution_time:.2f} seconds\n")
                f.write(f"Duplicate Handling: {self.duplicate_handling}\n\n")
            
            # Write announcements
            for i, announcement in enumerate(announcements, 1):
                f.write(f"Announcement {i}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Title: {announcement.title}\n")
                f.write(f"URL: {announcement.url}\n")
                f.write(f"Publication Date: {announcement.publication_date.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Extraction Time: {announcement.extraction_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"\nContent:\n{announcement.content_text}\n")
                
                if announcement.embedded_links:
                    f.write(f"\nEmbedded Links ({len(announcement.embedded_links)}):\n")
                    for j, link in enumerate(announcement.embedded_links, 1):
                        f.write(f"  {j}. {link.text} -> {link.url}\n")
                        if link.context:
                            f.write(f"     Context: {link.context}\n")
                
                f.write("\n" + "=" * 60 + "\n\n")
            
            # Write failed extractions if any and metadata is enabled
            if self.include_metadata and scraping_result.failed_extractions:
                f.write("Failed Extractions\n")
                f.write("=" * 20 + "\n\n")
                for failure in scraping_result.failed_extractions:
                    f.write(f"URL: {failure.url}\n")
                    f.write(f"Error: {failure.error_message}\n")
                    f.write(f"Type: {failure.error_type}\n")
                    f.write(f"Time: {failure.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        return output_path
    def _store_html(self, announcements: List[AnnouncementContent], 
                    scraping_result: ScrapingResult, filename: str) -> Path:
        """Store data in HTML format."""
        output_path = self.output_directory / f"{filename}.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            # Write HTML header
            f.write("""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Announcements Scraping Results</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #232f3e, #ff9900);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }
        .summary {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .summary h2 {
            color: #232f3e;
            margin-top: 0;
            border-bottom: 2px solid #ff9900;
            padding-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border-left: 4px solid #ff9900;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #232f3e;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        .announcement {
            background: white;
            margin-bottom: 30px;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            transition: transform 0.2s ease;
        }
        .announcement:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        .announcement-header {
            background: #232f3e;
            color: white;
            padding: 20px;
        }
        .announcement-title {
            margin: 0;
            font-size: 1.4em;
            font-weight: 500;
        }
        .announcement-meta {
            margin-top: 10px;
            opacity: 0.9;
            font-size: 0.9em;
        }
        .announcement-url {
            color: #ff9900;
            text-decoration: none;
            word-break: break-all;
        }
        .announcement-url:hover {
            text-decoration: underline;
        }
        .announcement-content {
            padding: 25px;
        }
        .content-text {
            white-space: pre-wrap;
            line-height: 1.7;
            margin-bottom: 20px;
            color: #444;
        }
        .embedded-links {
            margin-top: 20px;
        }
        .embedded-links h4 {
            color: #232f3e;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        .link-item {
            background: #f8f9fa;
            padding: 12px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 3px solid #ff9900;
        }
        .link-text {
            font-weight: 500;
            color: #232f3e;
        }
        .link-url {
            color: #0066cc;
            text-decoration: none;
            word-break: break-all;
            font-size: 0.9em;
        }
        .link-url:hover {
            text-decoration: underline;
        }
        .link-context {
            color: #666;
            font-size: 0.85em;
            margin-top: 5px;
            font-style: italic;
        }
        .metadata {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .metadata h3 {
            color: #232f3e;
            margin-top: 0;
            border-bottom: 2px solid #ff9900;
            padding-bottom: 10px;
        }
        .metadata-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .metadata-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
        }
        .metadata-label {
            font-weight: 500;
            color: #232f3e;
        }
        .metadata-value {
            color: #666;
            margin-top: 2px;
        }
        .failed-extractions {
            background: #fff5f5;
            border: 1px solid #fed7d7;
            border-radius: 8px;
            padding: 20px;
            margin-top: 20px;
        }
        .failed-extractions h4 {
            color: #c53030;
            margin-top: 0;
        }
        .failed-item {
            background: white;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 3px solid #c53030;
        }
        .search-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .search-input {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 5px;
            font-size: 16px;
            box-sizing: border-box;
        }
        .search-input:focus {
            outline: none;
            border-color: #ff9900;
        }
        .hidden {
            display: none;
        }
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            .header h1 {
                font-size: 2em;
            }
            .stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>AWS Announcements</h1>
        <p>Scraping Results</p>
    </div>
""")
            
            # Write summary section
            if self.include_metadata:
                f.write(f"""
    <div class="summary">
        <h2>Summary</h2>
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{len(announcements)}</div>
                <div class="stat-label">Successful Extractions</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{scraping_result.total_processed}</div>
                <div class="stat-label">Total Processed</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(scraping_result.failed_extractions)}</div>
                <div class="stat-label">Failed Extractions</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{scraping_result.execution_time:.1f}s</div>
                <div class="stat-label">Execution Time</div>
            </div>
        </div>
    </div>
""")
            
            # Add search functionality
            f.write("""
    <div class="search-box">
        <input type="text" class="search-input" placeholder="Search announcements by title or content..." 
               onkeyup="searchAnnouncements(this.value)">
    </div>
""")
            
            # Write announcements
            for i, announcement in enumerate(announcements, 1):
                # Escape HTML content
                title = self._escape_html(announcement.title)
                content_text = self._escape_html(announcement.content_text)
                url = self._escape_html(announcement.url)
                
                f.write(f"""
    <div class="announcement" data-search="{self._escape_html(announcement.title.lower() + ' ' + announcement.content_text.lower())}">
        <div class="announcement-header">
            <h3 class="announcement-title">{title}</h3>
            <div class="announcement-meta">
                <div><strong>URL:</strong> <a href="{url}" class="announcement-url" target="_blank">{url}</a></div>
                <div><strong>Published:</strong> {announcement.publication_date.strftime('%B %d, %Y')}</div>
                <div><strong>Extracted:</strong> {announcement.extraction_timestamp.strftime('%B %d, %Y at %H:%M:%S')}</div>
            </div>
        </div>
        <div class="announcement-content">
            <div class="content-text">{content_text}</div>
""")
                
                # Add embedded links if any
                if announcement.embedded_links:
                    f.write(f"""
            <div class="embedded-links">
                <h4>Embedded Links ({len(announcement.embedded_links)})</h4>
""")
                    for link in announcement.embedded_links:
                        link_text = self._escape_html(link.text)
                        link_url = self._escape_html(link.url)
                        link_context = self._escape_html(link.context) if link.context else ""
                        
                        f.write(f"""
                <div class="link-item">
                    <div class="link-text">{link_text}</div>
                    <div><a href="{link_url}" class="link-url" target="_blank">{link_url}</a></div>
""")
                        if link_context:
                            f.write(f'                    <div class="link-context">{link_context}</div>\n')
                        f.write('                </div>\n')
                    
                    f.write('            </div>\n')
                
                f.write('        </div>\n    </div>\n')
            
            # Write metadata section
            if self.include_metadata:
                f.write(f"""
    <div class="metadata">
        <h3>Extraction Metadata</h3>
        <div class="metadata-grid">
            <div class="metadata-item">
                <div class="metadata-label">Extraction Timestamp</div>
                <div class="metadata-value">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Scraper Version</div>
                <div class="metadata-value">1.0.0</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Output Format</div>
                <div class="metadata-value">{self.output_format}</div>
            </div>
            <div class="metadata-item">
                <div class="metadata-label">Duplicate Handling</div>
                <div class="metadata-value">{self.duplicate_handling}</div>
            </div>
""")
                
                # Add configuration details
                config_timeout = self.config.get('http', {}).get('timeout')
                config_retries = self.config.get('http', {}).get('max_retries')
                config_date_filter = self.config.get('filtering', {}).get('date_filter')
                
                if config_timeout:
                    f.write(f"""
            <div class="metadata-item">
                <div class="metadata-label">HTTP Timeout</div>
                <div class="metadata-value">{config_timeout}s</div>
            </div>
""")
                
                if config_retries:
                    f.write(f"""
            <div class="metadata-item">
                <div class="metadata-label">Max Retries</div>
                <div class="metadata-value">{config_retries}</div>
            </div>
""")
                
                if config_date_filter:
                    f.write(f"""
            <div class="metadata-item">
                <div class="metadata-label">Date Filter</div>
                <div class="metadata-value">{config_date_filter}</div>
            </div>
""")
                
                f.write('        </div>\n')
                
                # Add failed extractions if any
                if scraping_result.failed_extractions:
                    f.write(f"""
        <div class="failed-extractions">
            <h4>Failed Extractions ({len(scraping_result.failed_extractions)})</h4>
""")
                    for failure in scraping_result.failed_extractions:
                        f.write(f"""
            <div class="failed-item">
                <div><strong>URL:</strong> {self._escape_html(failure.url)}</div>
                <div><strong>Error:</strong> {self._escape_html(failure.error_message)}</div>
                <div><strong>Type:</strong> {failure.error_type}</div>
                <div><strong>Time:</strong> {failure.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</div>
            </div>
""")
                    f.write('        </div>\n')
                
                f.write('    </div>\n')
            
            # Add JavaScript for search functionality
            f.write("""
    <script>
        function searchAnnouncements(query) {
            const announcements = document.querySelectorAll('.announcement');
            const searchTerm = query.toLowerCase().trim();
            
            announcements.forEach(announcement => {
                const searchData = announcement.getAttribute('data-search');
                if (searchTerm === '' || searchData.includes(searchTerm)) {
                    announcement.classList.remove('hidden');
                } else {
                    announcement.classList.add('hidden');
                }
            });
            
            // Update visible count
            const visibleCount = document.querySelectorAll('.announcement:not(.hidden)').length;
            const totalCount = announcements.length;
            
            // You could add a results counter here if desired
            console.log(`Showing ${visibleCount} of ${totalCount} announcements`);
        }
    </script>
</body>
</html>
""")
        
        return output_path
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ""
        
        html_escape_table = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#x27;",
        }
        
        return "".join(html_escape_table.get(c, c) for c in text)