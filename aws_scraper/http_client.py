"""
HTTP client module for handling web requests with retry logic.

This module provides robust HTTP communication capabilities including
retry logic, rate limiting, and error handling.
"""

import logging
import random
import time
from typing import Optional, List
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HTTPClient:
    """HTTP client with session management and User-Agent rotation."""
    
    def __init__(self, timeout: int = 30):
        """
        Initialize HTTP client with session and configuration.
        
        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        
        # User-Agent strings for rotation
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
        # Set initial User-Agent
        self._rotate_user_agent()
        
        logger.info(f"HTTPClient initialized with timeout: {timeout}s")
    
    def _rotate_user_agent(self) -> None:
        """Rotate User-Agent header to appear as regular browser traffic."""
        user_agent = random.choice(self.user_agents)
        self.session.headers.update({'User-Agent': user_agent})
        logger.debug(f"Rotated User-Agent to: {user_agent}")
    
    def fetch_page(self, url: str, timeout: Optional[int] = None) -> requests.Response:
        """
        Fetch a single page with timeout handling.
        
        Args:
            url: URL to fetch
            timeout: Optional timeout override
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: For network or HTTP errors
        """
        if timeout is None:
            timeout = self.timeout
            
        logger.info(f"Fetching page: {url}")
        
        # Rotate User-Agent for each request
        self._rotate_user_agent()
        
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()  # Raise exception for bad status codes
            
            logger.info(f"Successfully fetched {url} - Status: {response.status_code}, Size: {len(response.content)} bytes")
            return response
            
        except requests.exceptions.Timeout:
            logger.error(f"Timeout occurred while fetching {url}")
            raise
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error occurred while fetching {url}")
            raise
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error {e.response.status_code} occurred while fetching {url}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception occurred while fetching {url}: {str(e)}")
            raise
    
    def fetch_with_retry(self, url: str, max_retries: int = 3, timeout: Optional[int] = None) -> requests.Response:
        """
        Fetch a page with retry logic and exponential backoff.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            timeout: Optional timeout override
            
        Returns:
            requests.Response object
            
        Raises:
            requests.RequestException: If all retry attempts fail
        """
        if timeout is None:
            timeout = self.timeout
            
        logger.info(f"Fetching page with retry: {url} (max_retries: {max_retries})")
        
        last_exception = None
        
        for attempt in range(max_retries + 1):  # +1 for initial attempt
            try:
                response = self.fetch_page(url, timeout)
                if attempt > 0:
                    logger.info(f"Successfully fetched {url} on attempt {attempt + 1}")
                return response
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                
                # Don't retry on certain status codes
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    
                    # Handle rate limiting (429) with progressive delays
                    if status_code == 429:
                        if attempt < max_retries:
                            delay = self._calculate_rate_limit_delay(attempt)
                            logger.warning(f"Rate limited (429) on {url}, waiting {delay}s before retry {attempt + 1}")
                            time.sleep(delay)
                            continue
                    
                    # Handle server errors (503, 502, 504) with exponential backoff
                    elif status_code in [502, 503, 504]:
                        if attempt < max_retries:
                            delay = self._calculate_exponential_backoff(attempt)
                            logger.warning(f"Server error {status_code} on {url}, waiting {delay}s before retry {attempt + 1}")
                            time.sleep(delay)
                            continue
                    
                    # Don't retry on client errors (4xx except 429)
                    elif 400 <= status_code < 500 and status_code != 429:
                        logger.error(f"Client error {status_code} on {url}, not retrying")
                        raise
                
                # Handle network errors (timeouts, connection errors) with exponential backoff
                elif isinstance(e, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
                    if attempt < max_retries:
                        delay = self._calculate_exponential_backoff(attempt)
                        logger.warning(f"Network error on {url}: {str(e)}, waiting {delay}s before retry {attempt + 1}")
                        time.sleep(delay)
                        continue
                
                # For other exceptions, don't retry
                logger.error(f"Non-retryable error on {url}: {str(e)}")
                raise
        
        # All retries exhausted
        logger.error(f"All {max_retries} retry attempts failed for {url}")
        raise last_exception
    
    def _calculate_exponential_backoff(self, attempt: int) -> float:
        """
        Calculate exponential backoff delay: 1s, 2s, 4s.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        return min(2 ** attempt, 4)  # Cap at 4 seconds
    
    def _calculate_rate_limit_delay(self, attempt: int) -> float:
        """
        Calculate progressive delay for rate limiting: 5s, 10s, 20s.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        delays = [5, 10, 20]
        return delays[min(attempt, len(delays) - 1)]