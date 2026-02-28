# AWS Announcements Scraper

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Python web scraping application that extracts content from AWS China's "Most Recent Announcements from Amazon Web Services" section. Features include date-based filtering, multiple output formats (JSON, CSV, TXT, HTML), and robust error handling.

## ✨ Features

- 🌐 **Bilingual Support**: Scrape both English and Chinese versions of AWS China website
- 🎯 **Smart Date Filtering**: Extract announcements by specific year/month (YYYY-MM format)
- 📊 **Multiple Output Formats**: JSON, CSV, plain text, and HTML with professional styling
- 🔄 **Robust Error Handling**: Automatic retries with exponential backoff
- ⚡ **Optimized Performance**: Filters before fetching to minimize requests (saves ~47 minutes on full scrapes)
- 📝 **Comprehensive Logging**: Detailed logs for debugging and monitoring
- ⚙️ **Highly Configurable**: Customize timeouts, retries, rate limiting, and more
- 🎨 **Professional HTML Reports**: Interactive search, AWS-themed styling, responsive design

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/neillidocker/aws-announcements-scraper.git
cd aws-announcements-scraper

# Install the package
pip install .

# Or install in development mode
pip install -e .
```

### Basic Usage

```bash
# Get announcements from January 2026 in HTML format (English version)
aws-scraper --date-filter 2026-01 --output-format html --output-dir ./results

# Get announcements from Chinese version
aws-scraper --language zh --date-filter 2026-01 --output-format html --output-dir ./results

# Get all announcements in JSON format
aws-scraper --output-format json --output-dir ./results

# Get announcements with custom configuration
aws-scraper --config config/aws_scraper_config.json --date-filter 2026-02

# Get announcements in CSV format with debug logging
aws-scraper --date-filter 2026-01 --output-format csv --log-level DEBUG
```

### Advanced Usage Examples

```bash
# Chinese version with all options
aws-scraper \
  --language zh \
  --date-filter 2026-01 \
  --output-format html \
  --output-dir ./results/chinese \
  --timeout 60 \
  --max-retries 5 \
  --rate-limit-delay 2 \
  --log-level INFO \
  --log-file scraper.log

# English version with custom timeout and retries
aws-scraper \
  --language en \
  --date-filter 2026-02 \
  --output-format json \
  --timeout 45 \
  --max-retries 5 \
  --output-dir ./results/february

# Dry run to test configuration
aws-scraper \
  --language zh \
  --date-filter 2026-01 \
  --output-format html \
  --dry-run

# Using configuration file
aws-scraper --config config/aws_scraper_config.json

# Multiple output formats for same data
aws-scraper --date-filter 2026-01 --output-format json --output-dir ./results
aws-scraper --date-filter 2026-01 --output-format html --output-dir ./results
aws-scraper --date-filter 2026-01 --output-format csv --output-dir ./results

# Bilingual reports
aws-scraper --language en --date-filter 2026-01 --output-dir ./reports/english
aws-scraper --language zh --date-filter 2026-01 --output-dir ./reports/chinese
```

## 📖 Documentation

### Command Line Options

| Option | Short | Description | Choices/Format | Default |
|--------|-------|-------------|----------------|---------|
| `--config` | `-c` | Path to configuration file | JSON or YAML file | None |
| `--language` | `-L` | Language version to scrape | en, english, zh, chinese | en |
| `--date-filter` | `-d` | Filter by year and month | YYYY-MM (e.g., 2026-01) | None (all) |
| `--output-format` | `-f` | Output file format | json, csv, txt, html | json |
| `--output-dir` | `-o` | Directory to save results | Valid directory path | ./output |
| `--timeout` | | HTTP request timeout in seconds | Positive integer | 300 |
| `--max-retries` | | Maximum retry attempts | Non-negative integer | 3 |
| `--rate-limit-delay` | | Delay between requests in seconds | Decimal number | 1.0 |
| `--log-level` | `-l` | Logging verbosity level | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO |
| `--log-file` | | Path to log file | File path | None (console only) |
| `--dry-run` | | Show what would be done without scraping | Flag | False |
| `--version` | | Show version and exit | Flag | - |
| `--help` | `-h` | Show help message and exit | Flag | - |

### Detailed Option Descriptions

#### Language Options
- `--language en` or `--language english`: Scrape English version (https://www.amazonaws.cn/en/new/)
- `--language zh` or `--language chinese`: Scrape Chinese version (https://www.amazonaws.cn/new/)

#### Date Filter
- Format: `YYYY-MM` (e.g., `2026-01` for January 2026)
- Filters announcements by publication date
- If not specified, all announcements are scraped

#### Output Formats
- `json`: Structured JSON with metadata
- `csv`: Comma-separated values for spreadsheet import
- `txt`: Plain text format for easy reading
- `html`: Professional HTML report with search functionality

#### HTTP Options
- `--timeout`: How long to wait for server response (seconds)
- `--max-retries`: How many times to retry failed requests
- `--rate-limit-delay`: Pause between requests to respect server (seconds, can be decimal like 1.5)

#### Logging Options
- `DEBUG`: Very detailed information for debugging
- `INFO`: General informational messages (recommended)
- `WARNING`: Warning messages only
- `ERROR`: Error messages only
- `CRITICAL`: Critical errors only

### Configuration File

Create a JSON or YAML configuration file to set default values:

#### JSON Configuration Example

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
    "rate_limit_delay": 1.0,
    "user_agents": [
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ]
  },
  "output": {
    "format": "json",
    "directory": "./results",
    "filename_template": "aws_announcements_{timestamp}",
    "include_metadata": true
  },
  "filtering": {
    "date_filter": "2026-01",
    "duplicate_handling": "skip"
  },
  "logging": {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": null
  }
}
```

#### YAML Configuration Example

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
  format: "json"  # json, csv, txt, or html
  directory: "./results"
  filename_template: "aws_announcements_{timestamp}"
  include_metadata: true

filtering:
  date_filter: "2026-01"  # YYYY-MM format
  duplicate_handling: "skip"  # skip, overwrite, or version

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: null  # null for console only, or specify file path
```

#### Using Configuration Files

```bash
# Use JSON config
aws-scraper --config config/aws_scraper_config.json

# Use YAML config
aws-scraper --config config/aws_scraper_config.yaml

# Override config with command-line options
aws-scraper --config config/aws_scraper_config.json --language zh --output-format html
```

**Note**: Command-line options override configuration file settings.

### Output Examples

#### JSON Output
```json
{
  "announcements": [
    {
      "title": "Amazon S3 now supports...",
      "url": "https://www.amazonaws.cn/...",
      "publication_date": "2026-01-31",
      "content_text": "Full announcement content...",
      "embedded_links": [...]
    }
  ],
  "metadata": {
    "total_announcements": 26,
    "extraction_timestamp": "2026-02-28T12:05:10",
    "date_filter": "2026-01"
  }
}
```

#### HTML Output
Professional, searchable HTML report with:
- Interactive search functionality
- AWS-themed styling
- Clickable links
- Summary statistics
- Responsive design

## 🏗️ Architecture

The system follows a layered architecture pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    CLI Interface                            │
├─────────────────────────────────────────────────────────────┤
│                Configuration Manager                        │
├─────────────────────────────────────────────────────────────┤
│                  Scraper Orchestrator                      │
├─────────────────────────────────────────────────────────────┤
│  Homepage Parser  │  Content Extractor  │  Date Filter    │
├─────────────────────────────────────────────────────────────┤
│              HTTP Client with Retry Logic                  │
├─────────────────────────────────────────────────────────────┤
│                    Data Storage Layer                      │
└─────────────────────────────────────────────────────────────┘
```

### Key Components

- **HTTP Client**: Handles all HTTP communication with retry logic and rate limiting
- **Homepage Parser**: Extracts announcement links from AWS homepage
- **Content Extractor**: Extracts structured content from individual pages
- **Date Filter**: Filters announcements by publication date
- **Data Storage**: Saves results in multiple formats

## 🧪 Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=aws_scraper --cov-report=html
```

### Project Structure

```
aws_scraper/
├── __init__.py              # Package initialization
├── models.py                # Data models
├── config_manager.py        # Configuration management
├── http_client.py           # HTTP client with retry logic
├── homepage_parser.py       # Homepage parsing
├── content_extractor.py     # Content extraction
├── date_filter.py           # Date filtering
├── data_storage.py          # Output formatting
├── scraper_orchestrator.py  # Main workflow
└── main.py                  # CLI interface
```

### Building Distribution Package

```bash
# Install build tools
pip install build

# Build the package
python -m build

# Or use the automated script
python build_distribution.py
```

## 📋 Requirements

- Python 3.8 or higher
- Internet connection to access AWS China website
- Dependencies:
  - requests >= 2.31.0
  - beautifulsoup4 >= 4.12.2
  - PyYAML >= 6.0.1

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Bug Reports & Feature Requests

- **Bug Reports**: [Open an issue](https://github.com/neillidocker/aws-announcements-scraper/issues)
- **Feature Requests**: [Open an issue](https://github.com/neillidocker/aws-announcements-scraper/issues)

## 📧 Contact

Your Name - ninamz@nwcdcloud.cn

Project Link: [https://github.com/neillidocker/aws-announcements-scraper](https://github.com/neillidocker/aws-announcements-scraper)

## 🙏 Acknowledgments

- AWS China for providing the announcements page
- BeautifulSoup for HTML parsing
- The Python community for excellent libraries

## 📊 Performance

- **Optimization**: Filters links before fetching content
- **Efficiency**: For date-filtered queries, only fetches relevant pages
- **Example**: January 2026 query fetches 26 pages instead of 420+ (saves ~47 minutes)
- **Execution Time**: ~4.5 minutes for monthly filtered queries vs ~52 minutes for full scrape

## 🔧 Troubleshooting

### Command not found after installation
```bash
# Solution: Use module syntax
python -m aws_scraper.main --date-filter 2026-01
```

### Network timeouts
```bash
# Solution: Increase timeout value
aws-scraper --timeout 60 --date-filter 2026-01
```

### Rate limiting errors
```bash
# Solution: Increase delay between requests
aws-scraper --delay 2 --date-filter 2026-01
```
---

Made with ❤️ by [Your Name]
