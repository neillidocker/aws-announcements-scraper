"""
Main entry point for the AWS announcements scraper.

This module provides the command-line interface and main execution logic
for the AWS announcements scraper application.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Optional

from .config_manager import ConfigurationManager
from .logging_config import setup_logging, get_logger


def validate_date_filter(date_string: str) -> str:
    """
    Validate date filter format (YYYY-MM).
    
    Args:
        date_string: Date string to validate
        
    Returns:
        Validated date string
        
    Raises:
        argparse.ArgumentTypeError: If date format is invalid
    """
    if not date_string:
        raise argparse.ArgumentTypeError("Date filter cannot be empty")
    
    # Check YYYY-MM format using regex
    pattern = r'^\d{4}-\d{2}$'
    if not re.match(pattern, date_string):
        raise argparse.ArgumentTypeError(
            f"Invalid date format '{date_string}'. Expected YYYY-MM format (e.g., 2026-01)"
        )
    
    # Validate year and month ranges
    try:
        year_str, month_str = date_string.split('-')
        year = int(year_str)
        month = int(month_str)
        
        # Basic year validation (reasonable range)
        if year < 2000 or year > 2100:
            raise argparse.ArgumentTypeError(
                f"Year {year} is outside reasonable range (2000-2100)"
            )
        
        # Month validation
        if month < 1 or month > 12:
            raise argparse.ArgumentTypeError(
                f"Month {month} is invalid. Must be between 01 and 12"
            )
        
        return date_string
        
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format '{date_string}'. Expected YYYY-MM format (e.g., 2026-01)"
        )


def validate_positive_int(value: str) -> int:
    """
    Validate positive integer values.
    
    Args:
        value: String value to validate
        
    Returns:
        Validated integer value
        
    Raises:
        argparse.ArgumentTypeError: If value is not a positive integer
    """
    try:
        int_value = int(value)
        if int_value <= 0:
            raise argparse.ArgumentTypeError(f"Value must be positive, got {int_value}")
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")


def validate_non_negative_int(value: str) -> int:
    """
    Validate non-negative integer values.
    
    Args:
        value: String value to validate
        
    Returns:
        Validated integer value
        
    Raises:
        argparse.ArgumentTypeError: If value is not a non-negative integer
    """
    try:
        int_value = int(value)
        if int_value < 0:
            raise argparse.ArgumentTypeError(f"Value must be non-negative, got {int_value}")
        return int_value
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid integer value: {value}")


def validate_output_directory(path_string: str) -> str:
    """
    Validate output directory path.
    
    Args:
        path_string: Directory path to validate
        
    Returns:
        Validated directory path
        
    Raises:
        argparse.ArgumentTypeError: If directory cannot be created or accessed
    """
    try:
        output_path = Path(path_string)
        # Try to create the directory if it doesn't exist
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Check if we can write to the directory
        if not output_path.is_dir():
            raise argparse.ArgumentTypeError(f"Path '{path_string}' is not a directory")
        
        # Test write permissions by creating a temporary file
        test_file = output_path / '.write_test'
        try:
            test_file.touch()
            test_file.unlink()  # Clean up
        except (PermissionError, OSError):
            raise argparse.ArgumentTypeError(f"No write permission for directory '{path_string}'")
        
        return str(output_path)
        
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid output directory '{path_string}': {e}")


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="AWS Announcements Scraper - Extract content from AWS China announcements",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage with default settings
  python -m aws_scraper.main
  
  # Use custom configuration file
  python -m aws_scraper.main --config config/aws_scraper_config.json
  
  # Filter announcements from January 2026 and save as CSV
  python -m aws_scraper.main --date-filter 2026-01 --output-format csv
  
  # Filter announcements from January 2026 and save as HTML
  python -m aws_scraper.main --date-filter 2026-01 --output-format html
  
  # Scrape Chinese version of the website
  python -m aws_scraper.main --language zh --date-filter 2026-01
  
  # Scrape Chinese version with HTML output
  python -m aws_scraper.main --language chinese --output-format html
  
  # Custom output directory with debug logging
  python -m aws_scraper.main --output-dir ./results --log-level DEBUG
  
  # Full configuration with all options
  python -m aws_scraper.main \\
    --config config/custom.yaml \\
    --date-filter 2026-02 \\
    --output-format json \\
    --output-dir ./output \\
    --timeout 45 \\
    --max-retries 5 \\
    --log-level INFO \\
    --log-file scraper.log

Date Filter Format:
  The date filter must be in YYYY-MM format:
  - 2026-01 (January 2026)
  - 2025-12 (December 2025)
  - 2024-06 (June 2024)

Configuration Files:
  Supports both JSON and YAML formats. The scraper will auto-detect
  the format based on file extension (.json, .yaml, .yml).
        """
    )
    
    # Configuration options
    config_group = parser.add_argument_group('Configuration Options')
    config_group.add_argument(
        '--config', '-c',
        type=str,
        metavar='PATH',
        help='Path to configuration file (JSON or YAML format)'
    )
    
    # Filtering options
    filter_group = parser.add_argument_group('Filtering Options')
    filter_group.add_argument(
        '--date-filter', '-d',
        type=validate_date_filter,
        metavar='YYYY-MM',
        help='Filter announcements by date (YYYY-MM format, e.g., 2026-01)'
    )
    filter_group.add_argument(
        '--language', '-L',
        choices=['en', 'zh', 'english', 'chinese'],
        default='en',
        metavar='LANG',
        help='Language version to scrape: en/english (English) or zh/chinese (Chinese) (default: en)'
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Options')
    output_group.add_argument(
        '--output-format', '-f',
        choices=['json', 'csv', 'txt', 'html'],
        metavar='FORMAT',
        help='Output format for results (choices: json, csv, txt, html)'
    )
    output_group.add_argument(
        '--output-dir', '-o',
        type=validate_output_directory,
        metavar='PATH',
        help='Output directory for results (will be created if it doesn\'t exist)'
    )
    
    # HTTP options
    http_group = parser.add_argument_group('HTTP Options')
    http_group.add_argument(
        '--timeout',
        type=validate_positive_int,
        metavar='SECONDS',
        help='HTTP request timeout in seconds (must be positive)'
    )
    http_group.add_argument(
        '--max-retries',
        type=validate_non_negative_int,
        metavar='COUNT',
        help='Maximum number of retry attempts (must be non-negative)'
    )
    http_group.add_argument(
        '--rate-limit-delay',
        type=float,
        metavar='SECONDS',
        help='Delay between requests in seconds (can be decimal, e.g., 1.5)'
    )
    
    # Logging options
    logging_group = parser.add_argument_group('Logging Options')
    logging_group.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    logging_group.add_argument(
        '--log-file',
        type=str,
        metavar='PATH',
        help='Log file path (default: console only)'
    )
    
    # Additional options
    misc_group = parser.add_argument_group('Miscellaneous Options')
    misc_group.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually scraping'
    )
    misc_group.add_argument(
        '--version',
        action='version',
        version='AWS Announcements Scraper 1.0.0'
    )
    
    return parser


def main() -> int:
    """Main entry point for the application."""
    parser = create_argument_parser()
    
    try:
        args = parser.parse_args()
    except SystemExit as e:
        # argparse calls sys.exit() on error, catch it to return proper exit code
        return e.code if e.code is not None else 1
    
    try:
        # Load configuration
        config_manager = ConfigurationManager(args.config)
        
        # Override config with command-line arguments
        config_overrides = {}
        
        # Normalize language parameter
        language = args.language if hasattr(args, 'language') else 'en'
        if language in ['chinese', 'zh']:
            language = 'zh'
        else:
            language = 'en'
        config_overrides['scraping.language'] = language
        
        if args.date_filter:
            config_overrides['filtering.date_filter'] = args.date_filter
        if args.output_format:
            config_overrides['output.format'] = args.output_format
        if args.output_dir:
            config_overrides['output.directory'] = args.output_dir
        if args.timeout:
            config_overrides['http.timeout'] = args.timeout
        if args.max_retries:
            config_overrides['http.max_retries'] = args.max_retries
        if args.rate_limit_delay is not None:
            if args.rate_limit_delay < 0:
                print("Error: Rate limit delay must be non-negative", file=sys.stderr)
                return 1
            config_overrides['http.rate_limit_delay'] = args.rate_limit_delay
        
        # Apply configuration overrides
        if config_overrides:
            config_manager.override_config(config_overrides)
        
        # Validate configuration
        if not config_manager.validate_config():
            print("Error: Configuration validation failed. Please check your settings.", file=sys.stderr)
            print("Use --help for usage information.", file=sys.stderr)
            return 1
        
        # Set up logging
        setup_logging(
            level=args.log_level,
            log_format=config_manager.get('logging.format'),
            log_file=args.log_file or config_manager.get('logging.file')
        )
        
        logger = get_logger(__name__)
        logger.info("AWS Announcements Scraper starting...")
        logger.info(f"Configuration loaded: {args.config or 'defaults'}")
        
        # Log configuration summary
        logger.info(f"Language: {config_manager.get('scraping.language', 'en').upper()}")
        if args.date_filter:
            logger.info(f"Date filter: {args.date_filter}")
        if args.output_format:
            logger.info(f"Output format: {args.output_format}")
        if args.output_dir:
            logger.info(f"Output directory: {args.output_dir}")
        
        # Handle dry-run mode
        if args.dry_run:
            logger.info("DRY RUN MODE - No actual scraping will be performed")
            logger.info("Configuration validation successful")
            logger.info("Would scrape AWS announcements with current settings")
            return 0
        
        # Initialize and run scraper orchestrator
        from .scraper_orchestrator import ScraperOrchestrator
        
        logger.info("Initializing scraper orchestrator...")
        orchestrator = ScraperOrchestrator(config_manager)
        
        # Run the complete scraping workflow
        logger.info("Starting scraping workflow...")
        result = orchestrator.run_scraping_workflow()
        
        # Report final results
        success_count = len(result.successful_extractions)
        failure_count = len(result.failed_extractions)
        total_time = result.execution_time
        
        logger.info(f"Scraping completed successfully!")
        logger.info(f"Results: {success_count} successful, {failure_count} failed")
        logger.info(f"Total execution time: {total_time:.2f} seconds")
        
        # Return appropriate exit code based on results
        if success_count == 0 and failure_count > 0:
            logger.error("No announcements were successfully extracted")
            return 1
        elif failure_count > 0:
            logger.warning(f"Some extractions failed ({failure_count} failures)")
            # Return 0 for partial success, but log the warnings
        
        return 0
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except FileNotFoundError as e:
        print(f"Error: Configuration file not found: {e}", file=sys.stderr)
        return 1
    except PermissionError as e:
        print(f"Error: Permission denied: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: Invalid configuration value: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())