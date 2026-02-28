"""
AWS Announcements Scraper - Setup Configuration
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "aws_scraper" / "README.md").read_text(encoding='utf-8')

setup(
    name="aws-announcements-scraper",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A web scraper for AWS China announcements with date filtering and multiple output formats",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/aws-announcements-scraper",
    packages=find_packages(exclude=["tests", "tests.*", "config", "results", "output"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.2",
        "PyYAML>=6.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "hypothesis>=6.92.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "aws-scraper=aws_scraper.main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
