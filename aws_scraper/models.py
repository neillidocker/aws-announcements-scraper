"""
Data models for the AWS announcements scraper.

This module defines the core data structures used throughout the application
for representing announcement links, content, and scraping results.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class AnnouncementLink:
    """Represents a link to an announcement found on the homepage."""
    title: str
    url: str
    preview_text: Optional[str] = None
    publication_date: Optional[datetime] = None


@dataclass
class EmbeddedLink:
    """Represents a link found within announcement content."""
    text: str
    url: str
    context: str  # Surrounding text for context


@dataclass
class AnnouncementContent:
    """Represents the full content extracted from an announcement page."""
    title: str
    url: str
    publication_date: datetime
    content_text: str
    embedded_links: List[EmbeddedLink]
    extraction_timestamp: datetime


@dataclass
class FailedExtraction:
    """Represents a failed attempt to extract content from a URL."""
    url: str
    error_message: str
    error_type: str
    timestamp: datetime


@dataclass
class ScrapingResult:
    """Represents the complete result of a scraping operation."""
    successful_extractions: List[AnnouncementContent]
    failed_extractions: List[FailedExtraction]
    total_processed: int
    execution_time: float