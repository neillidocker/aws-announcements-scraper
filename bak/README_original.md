# AWS Announcements Scraper

A Python web scraping application that extracts content from AWS China's "Most Recent Announcements from Amazon Web Services" section.

## Features

- 🌐 **Bilingual Support**: Scrape both English and Chinese versions of AWS China website
- 🎯 **Smart Date Filtering**: Extract announcements by specific year/month (YYYY-MM format)
- 📊 **Multiple Output Formats**: JSON, CSV, plain text, and HTML with professional styling
- 🔄 **Robust Error Handling**: Automatic retries with exponential backoff
- ⚡ **Optimized Performance**: Filters before fetching to minimize requests
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring
- ⚙️ **Highly Configurable**: Customize timeouts, retries, rate limiting, and more

## Project Structure

```
aws_scraper/
├── __init__.py                 # Package initialization and exports
├── models.py                   # Data models and structures
├── config_manager.py           # Configuration management
├── logging_config.py           # Logging setup and configuration
├── http_client.py              # HTTP client with retry logic
├── homepage_parser.py          # Homepage parsing functionality
├── content_extractor.py        # Content extraction from announcement pages
├── date_filter.py              # Date-based filtering
├── data_storage.py             # Data storage and output formatting
├── scraper_orchestrator.py     # Main workflow orchestrator
├── main.py                     # CLI interface and entry point
└── README.md                   # This file
```

## Quick Start

### Installation

```bash
# Install the package
pip install .

# Or install in development mode
pip install -e .
```

### Basic Usage

```bash
# After installation, use the aws-scraper command
aws-scraper --date-filter 2026-01 --output-format html

# Or use module syntax
python -m aws_scraper.main --date-filter 2026-01 --output-format html
```

## Command-Line Options

### Complete Options List

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Configuration file path (JSON/YAML) | None |
| `--language` | `-L` | Language: en, english, zh, chinese | en |
| `--date-filter` | `-d` | Filter by year-month (YYYY-MM) | None |
| `--output-format` | `-f` | Format: json, csv, txt, html | json |
| `--output-dir` | `-o` | Output directory | ./output |
| `--timeout` | | HTTP timeout (seconds) | 300 |
| `--max-retries` | | Maximum retry attempts | 3 |
| `--rate-limit-delay` | | Delay between requests (seconds) | 1.0 |
| `--log-level` | `-l` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO |
| `--log-file` | | Log file path | None |
| `--dry-run` | | Test without scraping | False |
| `--version` | | Show version | - |
| `--help` | `-h` | Show help | - |

## Usage Examples

### Basic Examples

```bash
# English version, January 2026, HTML format
python -m aws_scraper.main --date-filter 2026-01 --output-format html

# Chinese version, January 2026, JSON format
python -m aws_scraper.main --language zh --date-filter 2026-01 --output-format json

# All announcements, CSV format
python -m aws_scraper.main --output-format csv --output-dir ./results

# With debug logging
python -m aws_scraper.main --date-filter 2026-01 --log-level DEBUG
```

### Advanced Examples

```bash
# Chinese version with custom settings
python -m aws_scraper.main \
  --language zh \
  --date-filter 2026-01 \
  --output-format html \
  --output-dir ./results \
  --timeout 60 \
  --max-retries 5 \
  --rate-limit-delay 2 \
  --log-level INFO

# Using configuration file
python -m aws_scraper.main --config config/aws_scraper_config.json

# Dry run to test
python -m aws_scraper.main --language zh --date-filter 2026-01 --dry-run
```

## Configuration

The application supports both JSON and YAML configuration files.

### JSON Configuration Example

```json
{
  "scraping": {
    "language": "en",
    "base_urls": {
      "en": "https://www.amazonaws.cn/en/new/",
      "zh": "https://www.amazonaws.cn/new/"
    }
  },
  "http": {
    "timeout": 300,
    "max_retries": 3,
    "backoff_multiplier": 2,
    "rate_limit_delay": 1.0
  },
  "output": {
    "format": "json",
    "directory": "./output",
    "filename_template": "aws_announcements_{timestamp}",
    "include_metadata": true
  },
  "filtering": {
    "date_filter": null,
    "duplicate_handling": "skip"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": null
  }
}
```

### YAML Configuration Example

```yaml
scraping:
  language: "en"  # en for English, zh for Chinese
  base_urls:
    en: "https://www.amazonaws.cn/en/new/"
    zh: "https://www.amazonaws.cn/new/"

http:
  timeout: 300
  max_retries: 3
  backoff_multiplier: 2
  rate_limit_delay: 1.0

output:
  format: "json"
  directory: "./output"
  filename_template: "aws_announcements_{timestamp}"
  include_metadata: true

filtering:
  date_filter: null  # YYYY-MM format
  duplicate_handling: "skip"

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null
```

### Using Configuration Files

```bash
# Use JSON config
python -m aws_scraper.main --config config/aws_scraper_config.json

# Use YAML config
python -m aws_scraper.main --config config/aws_scraper_config.yaml

# Override config with command-line options
python -m aws_scraper.main --config config/base.json --language zh --output-format html
```

## Language Support

The scraper supports both English and Chinese versions of the AWS China website.

### English Version (Default)
```bash
python -m aws_scraper.main --language en --date-filter 2026-01
python -m aws_scraper.main --language english --date-filter 2026-01
```

### Chinese Version
```bash
python -m aws_scraper.main --language zh --date-filter 2026-01
python -m aws_scraper.main --language chinese --date-filter 2026-01
```

## Output Formats

### JSON
Structured JSON with metadata, ideal for programmatic processing.

### CSV
Comma-separated values, perfect for spreadsheet import and analysis.

### TXT
Plain text format, easy to read and share.

### HTML
Professional HTML report with:
- Interactive search functionality
- AWS-themed styling
- Clickable links
- Summary statistics
- Responsive design

## Dependencies

- **requests** >= 2.31.0: HTTP client functionality
- **beautifulsoup4** >= 4.12.2: HTML parsing
- **PyYAML** >= 6.0.1: YAML configuration support

### Development Dependencies
- **pytest** >= 7.4.3: Testing framework
- **hypothesis** >= 6.92.1: Property-based testing

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=aws_scraper --cov-report=html
```

## Architecture

The system follows a layered architecture:

1. **CLI Interface** (`main.py`) - Command-line argument parsing
2. **Configuration Manager** (`config_manager.py`) - Settings management
3. **Scraper Orchestrator** (`scraper_orchestrator.py`) - Workflow coordination
4. **Components**:
   - **Homepage Parser** (`homepage_parser.py`) - Extract announcement links
   - **Content Extractor** (`content_extractor.py`) - Extract page content
   - **Date Filter** (`date_filter.py`) - Filter by publication date
5. **HTTP Client** (`http_client.py`) - HTTP requests with retry logic
6. **Data Storage** (`data_storage.py`) - Save results in multiple formats

## Performance

- **Optimization**: Filters links before fetching content
- **Efficiency**: Only fetches relevant pages when date filtering is used
- **Example**: January 2026 query fetches ~26 pages instead of 400+ (saves ~47 minutes)
- **Execution Time**: ~25 seconds for monthly filtered queries vs ~52 minutes for full scrape

## Troubleshooting

### Command not found
```bash
# Use module syntax instead
python -m aws_scraper.main --date-filter 2026-01
```

### Network timeouts
```bash
# Increase timeout
python -m aws_scraper.main --timeout 60 --date-filter 2026-01
```

### Rate limiting errors
```bash
# Increase delay between requests
python -m aws_scraper.main --rate-limit-delay 2 --date-filter 2026-01
```

### Chinese characters not displaying
```bash
# Windows: Set UTF-8 encoding
chcp 65001
python -m aws_scraper.main --language zh --date-filter 2026-01

# Linux/Mac: Set locale
export LANG=en_US.UTF-8
python -m aws_scraper.main --language zh --date-filter 2026-01
```

## Development

### Building Distribution

```bash
# Install build tools
pip install build

# Build package
python -m build

# Or use automated script
python build_distribution.py
```

### Code Structure

- **models.py**: Data classes for announcements, links, and results
- **config_manager.py**: Configuration loading and validation
- **http_client.py**: HTTP requests with retry and rate limiting
- **homepage_parser.py**: Parse AWS homepage for announcement links
- **content_extractor.py**: Extract content from announcement pages
- **date_filter.py**: Filter announcements by publication date
- **data_storage.py**: Save results in multiple formats
- **scraper_orchestrator.py**: Coordinate the scraping workflow
- **main.py**: CLI interface and entry point

## Version

Current version: 1.0.0

## License

MIT License - See LICENSE file for details

## Related Documentation

- **README_GITHUB.md** - Complete GitHub documentation
- **AWS_SCRAPER_README.md** - User-friendly README
- **COMMAND_REFERENCE.md** - Detailed command reference
- **LANGUAGE_SUPPORT.md** - Language feature guide
- **DISTRIBUTION_GUIDE.md** - Distribution instructions