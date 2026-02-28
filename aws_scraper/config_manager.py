"""
Configuration management module for application settings.

This module handles loading, validation, and management of configuration
settings from JSON/YAML files with appropriate defaults.
"""

import json
import logging
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import copy

logger = logging.getLogger(__name__)


class ConfigurationManager:
    """Manages application configuration settings."""
    
    DEFAULT_CONFIG = {
        "scraping": {
            "language": "en",  # en for English, zh for Chinese
            "base_urls": {
                "en": "https://www.amazonaws.cn/en/new/",
                "zh": "https://www.amazonaws.cn/new/"
            }
        },
        "http": {
            "timeout": 300,
            "max_retries": 3,
            "backoff_multiplier": 2,
            "rate_limit_delay": 1.0,
            "user_agents": [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ]
        },
        "output": {
            "format": "json",
            "directory": "./output",
            "filename_template": "aws_announcements_{timestamp}",
            "include_metadata": True
        },
        "filtering": {
            "date_filter": None,  # YYYY-MM format
            "duplicate_handling": "skip"  # skip, overwrite, version
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file": None  # None for console only, or specify file path
        }
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager with optional config file path."""
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, config_path: str) -> None:
        """Load configuration from JSON or YAML file."""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"Configuration file {config_path} not found, using defaults")
                return
            
            with open(config_file, 'r', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    user_config = yaml.safe_load(f)
                else:
                    user_config = json.load(f)
            
            # Merge user config with defaults
            self._merge_config(self.config, user_config)
            logger.info(f"Configuration loaded from {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            logger.info("Using default configuration")
    
    def _merge_config(self, default: Dict[Any, Any], user: Dict[Any, Any]) -> None:
        """Recursively merge user configuration with defaults."""
        for key, value in user.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                self._merge_config(default[key], value)
            else:
                default[key] = value
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'http.timeout')."""
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> None:
        """Set configuration value using dot notation (e.g., 'http.timeout')."""
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the final value
        config[keys[-1]] = value
        logger.debug(f"Configuration updated: {key_path} = {value}")
    
    def override_config(self, overrides: Dict[str, Any]) -> None:
        """Override configuration with provided key-value pairs using dot notation."""
        for key_path, value in overrides.items():
            self.set(key_path, value)
        logger.info(f"Configuration overridden with {len(overrides)} settings")
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration dictionary."""
        return self.config.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self.config = copy.deepcopy(self.DEFAULT_CONFIG)
        logger.info("Configuration reset to defaults")
    
    def save_config(self, config_path: str) -> None:
        """Save current configuration to file (JSON or YAML based on extension)."""
        try:
            config_file = Path(config_path)
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(config_file, 'w', encoding='utf-8') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration to {config_path}: {e}")
            raise
    
    def validate_config(self) -> bool:
        """Validate configuration settings and return True if valid."""
        try:
            # Validate HTTP settings
            if self.get('http.timeout') <= 0:
                logger.error("HTTP timeout must be positive")
                return False
            
            if self.get('http.max_retries') < 0:
                logger.error("Max retries must be non-negative")
                return False
            
            if self.get('http.backoff_multiplier') <= 1:
                logger.error("Backoff multiplier must be greater than 1")
                return False
            
            if self.get('http.rate_limit_delay') < 0:
                logger.error("Rate limit delay must be non-negative")
                return False
            
            # Validate output format
            valid_formats = ['json', 'csv', 'txt', 'html']
            if self.get('output.format') not in valid_formats:
                logger.error(f"Output format must be one of: {valid_formats}")
                return False
            
            # Validate output directory
            output_dir = self.get('output.directory')
            if output_dir:
                try:
                    Path(output_dir).mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"Cannot create output directory {output_dir}: {e}")
                    return False
            
            # Validate duplicate handling
            valid_duplicate_handling = ['skip', 'overwrite', 'version']
            if self.get('filtering.duplicate_handling') not in valid_duplicate_handling:
                logger.error(f"Duplicate handling must be one of: {valid_duplicate_handling}")
                return False
            
            # Validate date filter format if provided
            date_filter = self.get('filtering.date_filter')
            if date_filter:
                try:
                    # Validate YYYY-MM format
                    parts = date_filter.split('-')
                    if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
                        raise ValueError("Invalid format")
                    int(parts[0])  # Year
                    month = int(parts[1])  # Month
                    if not 1 <= month <= 12:
                        raise ValueError("Invalid month")
                except ValueError:
                    logger.error("Date filter must be in YYYY-MM format")
                    return False
            
            # Validate logging level
            valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            if self.get('logging.level') not in valid_log_levels:
                logger.error(f"Logging level must be one of: {valid_log_levels}")
                return False
            
            # Validate language setting
            valid_languages = ['en', 'zh']
            if self.get('scraping.language') not in valid_languages:
                logger.error(f"Language must be one of: {valid_languages}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False