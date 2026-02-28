"""
AWS Announcements Scraper Package

A web scraping application that captures content from AWS China's 
"Most Recent Announcements from Amazon Web Services" section.
"""

__version__ = "1.0.0"
__author__ = "AWS Scraper Team"

# Package-level imports for convenience
from .scraper_orchestrator import ScraperOrchestrator
from .content_extractor import ContentExtractor
from .models import AnnouncementLink, AnnouncementContent, ScrapingResult

__all__ = [
    "ScraperOrchestrator",
    "ContentExtractor",
    "AnnouncementLink", 
    "AnnouncementContent",
    "ScrapingResult"
]