"""
Date filtering module for announcement filtering by date.

This module provides functionality to filter announcements based on
publication date criteria using YYYY-MM format.
"""

import logging
import re
from datetime import datetime
from typing import List, Optional

from .models import AnnouncementContent

logger = logging.getLogger(__name__)


class DateFilter:
    """Handles date-based filtering of announcements."""
    
    def __init__(self):
        """Initialize the DateFilter."""
        self.date_pattern = re.compile(r'^\d{4}-\d{2}$')
    
    def parse_date_filter(self, date_string: str) -> Optional[tuple]:
        """
        Parse date filter string in YYYY-MM format.
        
        Args:
            date_string: Date string in YYYY-MM format (e.g., "2026-01")
            
        Returns:
            Tuple of (year, month) if valid, None if invalid
            
        Raises:
            ValueError: If date format is invalid
        """
        if not date_string:
            return None
            
        if not self.date_pattern.match(date_string):
            raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM format (e.g., '2026-01')")
        
        try:
            year, month = date_string.split('-')
            year = int(year)
            month = int(month)
            
            # Validate month range
            if month < 1 or month > 12:
                raise ValueError(f"Invalid month: {month}. Month must be between 1 and 12")
            
            # Validate year range (reasonable bounds)
            if year < 2000 or year > 2100:
                raise ValueError(f"Invalid year: {year}. Year must be between 2000 and 2100")
                
            logger.debug(f"Parsed date filter: year={year}, month={month}")
            return (year, month)
            
        except ValueError as e:
            if "invalid literal" in str(e):
                raise ValueError(f"Invalid date format: {date_string}. Expected YYYY-MM format (e.g., '2026-01')")
            raise
    
    def matches_date_criteria(self, announcement_date: datetime, target_year: int, target_month: int) -> bool:
        """
        Check if an announcement date matches the filtering criteria.
        
        Args:
            announcement_date: The publication date of the announcement
            target_year: Target year for filtering
            target_month: Target month for filtering
            
        Returns:
            True if the announcement matches the date criteria, False otherwise
        """
        if not announcement_date:
            logger.warning("Announcement has no publication date, excluding from filtered results")
            return False
            
        matches = (announcement_date.year == target_year and 
                  announcement_date.month == target_month)
        
        logger.debug(f"Date match check: {announcement_date.strftime('%Y-%m')} vs {target_year:04d}-{target_month:02d} = {matches}")
        return matches
    
    def filter_by_date(self, announcements: List[AnnouncementContent], date_filter: Optional[str] = None) -> List[AnnouncementContent]:
        """
        Filter announcements by publication date.
        
        Args:
            announcements: List of announcements to filter
            date_filter: Date filter string in YYYY-MM format, or None to return all
            
        Returns:
            Filtered list of announcements matching the date criteria
            
        Raises:
            ValueError: If date_filter format is invalid
        """
        if not date_filter:
            logger.info("No date filter specified, returning all announcements")
            return announcements
        
        # Parse the date filter
        parsed_date = self.parse_date_filter(date_filter)
        if not parsed_date:
            return announcements
            
        target_year, target_month = parsed_date
        
        # Filter announcements
        filtered_announcements = []
        for announcement in announcements:
            if self.matches_date_criteria(announcement.publication_date, target_year, target_month):
                filtered_announcements.append(announcement)
        
        logger.info(f"Date filtering complete: {len(filtered_announcements)}/{len(announcements)} announcements match {date_filter}")
        return filtered_announcements