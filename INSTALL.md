# Installation Guide

This guide provides detailed installation instructions for Smart AI Scraper on different platforms.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation Methods](#installation-methods)
- [Platform-Specific Instructions](#platform-specific-instructions)
- [Post-Installation](#post-installation)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.9 or higher
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space
- Internet connection

### Required Services

- **Redis** (for distributed scraping)
- **MongoDB** or **PostgreSQL** (for data storage)

## Installation Methods

### Method 1: Quick Install (Recommended)

```bash
# Clone the repository
git clone https://github.com/maidulcu/smart-ai-scraper.git
cd smart-ai-scraper

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .

# Run setup assistant
smart-scraper setup
```

### Method 2: Using pip (when published)

```bash
# Install from PyPI
pip install smart-ai-scraper

# Run setup
smart-scraper setup
```

### Method 3: Using Docker (coming soon)

```bash
docker-compose up -d
```

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Redis
sudo apt install redis-server -y
sudo systemctl start redis
sudo systemctl enable redis

# Install MongoDB
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu $(lsb_release -cs)/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list
sudo apt update
sudo apt install mongodb-org -y
sudo systemctl start mongod
sudo systemctl enable mongod

# Clone and install Smart AI Scraper
git clone https://github.com/maidulcu/smart-ai-scraper.git
cd smart-ai-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Install Playwright browsers
playwright install chromium

# Download spaCy model
python -m spacy download en_core_web_sm

# Run setup
smart-scraper setup
```

### macOS

```bash
# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python
brew install python@3.11

# Install Redis
brew install redis
brew services start redis

# Install MongoDB
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Clone and install Smart AI Scraper
git clone https://github.com/maidulcu/smart-ai-scraper.git
cd smart-ai-scraper
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Install Playwright browsers
playwright install chromium

# Download spaCy model
python -m spacy download en_core_web_sm

# Run setup
smart-scraper setup
```

### Windows

1. **Install Python**
   - Download from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation

2. **Install Redis**
   - Download from https://github.com/microsoftarchive/redis/releases
   - Extract and run `redis-server.exe`

3. **Install MongoDB**
   - Download from https://www.mongodb.com/try/download/community
   - Install as a service

4. **Install Smart AI Scraper**
   ```powershell
   # Clone repository
   git clone https://github.com/maidulcu/smart-ai-scraper.git
   cd smart-ai-scraper

   # Create virtual environment
   python -m venv venv
   venv\Scripts\activate

   # Install dependencies
   pip install -r requirements.txt
   pip install -e .

   # Install Playwright browsers
   playwright install chromium

   # Download spaCy model
   python -m spacy download en_core_web_sm

   # Run setup
   smart-scraper setup
   ```

## Virtual Environment (Recommended)

Using a virtual environment isolates dependencies:

```bash
# Create virtual environment
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Post-Installation

### 1. Configuration

Create a `.env` file in the project root:

```bash
cp config/default.env .env
```

Edit `.env` to configure:
- Database connection
- Browser settings
- Rate limiting
- Ethical scraping options

### 2. Download AI Models

```bash
# Download spaCy model
python -m spacy download en_core_web_sm

# Optional: Download larger model for better accuracy
python -m spacy download en_core_web_md
```

### 3. Install Browser

```bash
# Install Chromium
playwright install chromium

# Optional: Install other browsers
playwright install firefox
playwright install webkit
```

### 4. Setup Database

**MongoDB:**
```bash
# Connect to MongoDB
mongosh

# Create database
use smart_scraper

# Create user (optional)
db.createUser({
  user: "scraper",
  pwd: "password",
  roles: ["readWrite"]
})
```

**PostgreSQL:**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE smart_scraper;

# Create user (optional)
CREATE USER scraper WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE smart_scraper TO scraper;
```

## Verification

Test your installation:

```bash
# Check installation
smart-scraper --version

# View configuration
smart-scraper config

# Test scraping (with a safe URL)
smart-scraper scrape https://example.com
```

## Troubleshooting

### Playwright Installation Failed

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 libcairo2

# Reinstall Playwright
pip install --force-reinstall playwright
playwright install chromium
```

### spaCy Model Not Found

```bash
# Verify installation
python -m spacy info

# Download model again
python -m spacy download en_core_web_sm --force
```

### Redis Connection Error

```bash
# Check if Redis is running
redis-cli ping
# Should return: PONG

# Start Redis
# Linux:
sudo systemctl start redis

# macOS:
brew services start redis

# Windows:
redis-server.exe
```

### MongoDB Connection Error

```bash
# Check if MongoDB is running
mongosh --eval "db.version()"

# Start MongoDB
# Linux:
sudo systemctl start mongod

# macOS:
brew services start mongodb-community

# Windows:
net start MongoDB
```

### Import Errors

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check Python version
python --version
# Should be 3.9 or higher
```

### Permission Errors (Linux/macOS)

```bash
# Use virtual environment instead of system Python
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Updating

To update to the latest version:

```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Reinstall package
pip install -e .

# Update Playwright
playwright install chromium

# Update spaCy models
python -m spacy download en_core_web_sm --upgrade
```

## Uninstalling

```bash
# Uninstall package
pip uninstall smart-ai-scraper

# Remove virtual environment
rm -rf venv

# Optional: Remove databases and Redis data
# (Be careful - this deletes all scraped data!)
```

## Additional Resources

- [README.md](README.md) - Main documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [Examples](examples/) - Usage examples
- [GitHub Issues](https://github.com/maidulcu/smart-ai-scraper/issues) - Support

## Next Steps

After installation:

1. Read the [README.md](README.md) for usage instructions
2. Try the examples in the `examples/` directory
3. Configure your settings in `.env`
4. Start scraping!

For questions or issues, please create an issue on GitHub.
