"""
Homepage parser module for extracting announcement links.

This module handles parsing of the AWS homepage to identify and extract
announcement links from the "Most Recent Announcements" section.
"""

import logging
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag

from .models import AnnouncementLink

logger = logging.getLogger(__name__)


class HomepageParser:
    """Parser for extracting announcement links from AWS homepage."""
    
    def __init__(self, base_url: str = "https://www.amazonaws.cn/en/new/"):
        """
        Initialize the homepage parser.
        
        Args:
            base_url: Base URL for resolving relative links
        """
        self.base_url = base_url
        logger.debug(f"HomepageParser initialized with base_url: {base_url}")
    
    def parse_homepage(self, html_content: str) -> List[AnnouncementLink]:
        """
        Parse the AWS homepage and extract announcement links.
        
        Args:
            html_content: Raw HTML content of the homepage
            
        Returns:
            List of AnnouncementLink objects found in the announcements section
            
        Raises:
            ValueError: If the announcements section cannot be found
        """
        logger.info("Starting homepage parsing")
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            announcements_section = self.find_announcements_section(soup)
            
            if announcements_section is None:
                error_msg = "Could not find 'Most Recent Announcements from Amazon Web Services' section"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            announcement_links = self.extract_announcement_links(announcements_section)
            logger.info(f"Successfully extracted {len(announcement_links)} announcement links")
            
            return announcement_links
            
        except Exception as e:
            logger.error(f"Error parsing homepage: {str(e)}")
            raise
    
    def find_announcements_section(self, soup: BeautifulSoup) -> Optional[Tag]:
        """
        Find the "Most Recent Announcements from Amazon Web Services" section.
        
        Args:
            soup: BeautifulSoup object of the parsed HTML
            
        Returns:
            Tag containing the announcements section, or the entire document if JSON data is found
        """
        logger.debug("Searching for announcements section")
        
        # First check if we have JSON data embedded in the page
        page_content = str(soup)
        if '"itemTitle"' in page_content and '"itemLink"' in page_content:
            logger.debug("Found JSON announcement data in page")
            return soup  # Return the entire document for JSON parsing
        
        # Search for text containing "Most Recent Announcements from Amazon Web Services"
        target_text = "Most Recent Announcements from Amazon Web Services"
        
        # Look for headings or elements containing this text
        for element in soup.find_all(string=lambda text: text and target_text in text):
            # Get the parent element that likely contains the section
            parent = element.parent
            
            # Walk up the DOM to find a suitable container
            current = parent
            for _ in range(5):  # Limit search depth
                if current is None:
                    break
                    
                # Look for common section containers
                if current.name in ['div', 'section', 'article'] and current.find_all('a'):
                    logger.debug(f"Found announcements section in {current.name} tag")
                    return current
                    
                current = current.parent
        
        # Alternative search: look for sections with multiple links that might be announcements
        logger.debug("Primary search failed, trying alternative approach")
        
        # Look for containers with multiple links that could be announcements
        potential_sections = soup.find_all(['div', 'section', 'ul'], 
                                         class_=lambda x: x and any(keyword in x.lower() 
                                                                   for keyword in ['news', 'announcement', 'recent', 'latest']))
        
        for section in potential_sections:
            links = section.find_all('a', href=True)
            if len(links) >= 3:  # Assume announcements section has multiple links
                logger.debug(f"Found potential announcements section with {len(links)} links")
                return section
        
        # If no specific section found but we have JSON data, return the entire document
        if '"itemTitle"' in page_content:
            logger.debug("No specific section found, but JSON data detected - returning entire document")
            return soup
        
        logger.warning("Could not find announcements section")
        return None
    
    def extract_announcement_links(self, section: Tag) -> List[AnnouncementLink]:
        """
        Extract announcement links from the given section.
        
        Args:
            section: BeautifulSoup Tag containing the announcements
            
        Returns:
            List of AnnouncementLink objects
        """
        logger.debug("Extracting announcement links from section")
        
        links = []
        
        # First try to extract from JSON data embedded in the page
        json_links = self._extract_from_json_data(section)
        if json_links:
            logger.info(f"Extracted {len(json_links)} links from JSON data")
            return json_links
        
        # Fallback to HTML parsing if JSON extraction fails
        anchor_tags = section.find_all('a', href=True)
        
        for anchor in anchor_tags:
            try:
                href = anchor.get('href', '').strip()
                if not href:
                    continue
                
                # Resolve relative URLs
                full_url = self._resolve_url(href)
                
                # Skip if URL doesn't look like an announcement
                if not self._is_announcement_url(full_url):
                    logger.debug(f"Skipping non-announcement URL: {full_url}")
                    continue
                
                # Extract title from link text or title attribute
                title = self._extract_link_title(anchor)
                if not title:
                    logger.debug(f"Skipping link with no title: {full_url}")
                    continue
                
                # Extract preview text if available
                preview_text = self._extract_preview_text(anchor)
                
                announcement_link = AnnouncementLink(
                    title=title,
                    url=full_url,
                    preview_text=preview_text
                )
                
                links.append(announcement_link)
                logger.debug(f"Extracted link: {title} -> {full_url}")
                
            except Exception as e:
                logger.warning(f"Error processing link {anchor}: {str(e)}")
                continue
        
        logger.info(f"Extracted {len(links)} valid announcement links")
        return links
    
    def _resolve_url(self, href: str) -> str:
        """Resolve relative URLs to absolute URLs."""
        if href.startswith(('http://', 'https://')):
            return href
        return urljoin(self.base_url, href)
    
    def _is_announcement_url(self, url: str) -> bool:
        """
        Check if URL looks like an announcement URL.
        
        This filters out navigation links, external links, etc.
        """
        try:
            parsed = urlparse(url)
            
            # Skip external links (different domain)
            if parsed.netloc and 'amazonaws.cn' not in parsed.netloc:
                return False
            
            # Skip common non-announcement paths
            skip_patterns = [
                '/about/', '/contact/', '/support/', '/pricing/',
                '/documentation/', '/console/', '/signin/', '/signup/',
                'javascript:', 'mailto:', '#'
            ]
            
            path = parsed.path.lower()
            for pattern in skip_patterns:
                if pattern in path:
                    return False
            
            # Announcement URLs typically contain certain patterns
            announcement_patterns = [
                '/new/', '/announcement/', '/blog/', '/press/',
                '/release/', '/update/', '/launch/'
            ]
            
            for pattern in announcement_patterns:
                if pattern in path:
                    return True
            
            # If it has a meaningful path (not just root), consider it
            return len(path) > 1 and path != '/'
            
        except Exception:
            return False
    
    def _extract_link_title(self, anchor: Tag) -> str:
        """Extract title from anchor tag."""
        # Try title attribute first
        title = anchor.get('title', '').strip()
        if title:
            return title
        
        # Try link text
        text = anchor.get_text(strip=True)
        if text:
            return text
        
        # Try alt text from images
        img = anchor.find('img')
        if img:
            alt_text = img.get('alt', '').strip()
            if alt_text:
                return alt_text
        
        return ""
    
    def _extract_preview_text(self, anchor: Tag) -> Optional[str]:
        """Extract preview text near the link if available."""
        # Look for preview text in nearby elements
        parent = anchor.parent
        if parent:
            # Check for description in sibling elements
            for sibling in parent.find_next_siblings():
                text = sibling.get_text(strip=True)
                if text and len(text) > 20:  # Meaningful preview text
                    return text[:200]  # Limit length
                    
            # Check for description in parent's text
            parent_text = parent.get_text(strip=True)
            link_text = anchor.get_text(strip=True)
            if parent_text and link_text in parent_text:
                # Extract text after the link
                remaining = parent_text.split(link_text, 1)
                if len(remaining) > 1 and remaining[1].strip():
                    preview = remaining[1].strip()
                    return preview[:200] if len(preview) > 20 else None
        
        return None
    
    def _extract_from_json_data(self, section: Tag) -> List[AnnouncementLink]:
        """
        Extract announcement links from JSON data embedded in the page.
        
        Args:
            section: BeautifulSoup Tag (could be the entire document)
            
        Returns:
            List of AnnouncementLink objects extracted from JSON data
        """
        import json
        import re
        
        logger.debug("Attempting to extract announcements from JSON data")
        
        # Get the entire page content to search for JSON data
        page_content = str(section.find_parent('html') or section)
        
        # Look for JSON data containing announcement information
        # Pattern to find JSON objects with announcement-like structure
        json_patterns = [
            r'"fields":\s*{[^}]*"itemTitle":[^}]+}',
            r'{[^}]*"itemTitle":[^}]*"itemBody":[^}]*"itemLink":[^}]*}',
        ]
        
        announcements = []
        
        for pattern in json_patterns:
            matches = re.findall(pattern, page_content, re.DOTALL)
            
            for match in matches:
                try:
                    # Try to extract a complete JSON object containing this match
                    # Find the start and end of the JSON object
                    start_pos = page_content.find(match)
                    if start_pos == -1:
                        continue
                    
                    # Look backwards to find the opening brace
                    brace_count = 0
                    json_start = start_pos
                    while json_start > 0:
                        char = page_content[json_start]
                        if char == '}':
                            brace_count += 1
                        elif char == '{':
                            if brace_count == 0:
                                break
                            brace_count -= 1
                        json_start -= 1
                    
                    # Look forwards to find the closing brace
                    brace_count = 0
                    json_end = start_pos + len(match)
                    while json_end < len(page_content):
                        char = page_content[json_end]
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            if brace_count == 0:
                                json_end += 1
                                break
                            brace_count -= 1
                        json_end += 1
                    
                    # Extract and parse the JSON
                    json_str = page_content[json_start:json_end]
                    
                    try:
                        data = json.loads(json_str)
                        announcement = self._parse_announcement_from_json(data)
                        if announcement:
                            announcements.append(announcement)
                    except json.JSONDecodeError:
                        # Try to find a larger JSON structure
                        continue
                        
                except Exception as e:
                    logger.debug(f"Error parsing JSON match: {e}")
                    continue
        
        # If we didn't find individual announcements, look for a larger data structure
        if not announcements:
            announcements = self._extract_from_large_json_structure(page_content)
        
        # Remove duplicates based on URL
        seen_urls = set()
        unique_announcements = []
        for announcement in announcements:
            if announcement.url not in seen_urls:
                seen_urls.add(announcement.url)
                unique_announcements.append(announcement)
        
        logger.debug(f"Extracted {len(unique_announcements)} unique announcements from JSON")
        return unique_announcements
    
    def _extract_from_large_json_structure(self, page_content: str) -> List[AnnouncementLink]:
        """
        Extract announcements from large JSON data structures in the page.
        
        Args:
            page_content: The entire page content as string
            
        Returns:
            List of AnnouncementLink objects
        """
        import json
        import re
        
        announcements = []
        
        # Look for large JSON structures that might contain announcement data
        # Pattern to find JSON arrays or objects with multiple announcement items
        large_json_pattern = r'{"data":\s*{"items":\s*\[[^\]]*"itemTitle"[^\]]*\]'
        
        matches = re.findall(large_json_pattern, page_content, re.DOTALL)
        
        for match in matches:
            try:
                # Find the complete JSON structure
                start_pos = page_content.find(match)
                if start_pos == -1:
                    continue
                
                # Find the end of this JSON structure
                brace_count = 0
                json_end = start_pos
                for i, char in enumerate(page_content[start_pos:]):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            json_end = start_pos + i + 1
                            break
                
                json_str = page_content[start_pos:json_end]
                
                try:
                    data = json.loads(json_str)
                    
                    # Navigate the JSON structure to find announcement items
                    items = []
                    if isinstance(data, dict):
                        if 'data' in data and 'items' in data['data']:
                            items = data['data']['items']
                        elif 'items' in data:
                            items = data['items']
                    
                    for item in items:
                        announcement = self._parse_announcement_from_json(item)
                        if announcement:
                            announcements.append(announcement)
                            
                except json.JSONDecodeError as e:
                    logger.debug(f"Failed to parse large JSON structure: {e}")
                    continue
                    
            except Exception as e:
                logger.debug(f"Error processing large JSON structure: {e}")
                continue
        
        return announcements
    
    def _parse_announcement_from_json(self, data: dict) -> Optional[AnnouncementLink]:
        """
        Parse an announcement from a JSON data structure.
        
        Args:
            data: Dictionary containing announcement data
            
        Returns:
            AnnouncementLink object or None if parsing fails
        """
        try:
            # Look for announcement data in various possible structures
            fields = data.get('fields', data)
            
            # Extract title
            title = fields.get('itemTitle', fields.get('title', fields.get('heading', '')))
            if not title:
                return None
            
            # Extract URL
            url = fields.get('itemLink', fields.get('url', fields.get('linkURL', '')))
            if not url:
                return None
            
            # Resolve relative URLs
            full_url = self._resolve_url(url)
            
            # Extract preview text
            preview_text = fields.get('itemBody', fields.get('body', fields.get('subheading', '')))
            if preview_text:
                # Clean up HTML tags and limit length
                import re
                preview_text = re.sub(r'<[^>]+>', '', preview_text)
                preview_text = preview_text.strip()
                if len(preview_text) > 200:
                    preview_text = preview_text[:200] + '...'
            
            # Extract publication date from JSON metadata
            publication_date = None
            publication_date_str = fields.get('itemMetadataDate', '')
            if publication_date_str:
                # Format: "2025-12-06T00:00:00.000+08:00" -> datetime object
                import re
                from datetime import datetime
                
                date_match = re.match(r'(\d{4}-\d{2}-\d{2})', publication_date_str)
                if date_match:
                    date_str = date_match.group(1)
                    try:
                        publication_date = datetime.strptime(date_str, '%Y-%m-%d')
                        logger.debug(f"Parsed publication date: {publication_date} from {publication_date_str}")
                    except ValueError as e:
                        logger.debug(f"Failed to parse date {date_str}: {e}")
            
            return AnnouncementLink(
                title=title.strip(),
                url=full_url,
                preview_text=preview_text if preview_text else None,
                publication_date=publication_date
            )
            
        except Exception as e:
            logger.debug(f"Error parsing announcement from JSON: {e}")
            return None