# Contributing to Smart AI Scraper

Thank you for your interest in contributing to Smart AI Scraper! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect differing viewpoints and experiences

## How to Contribute

### Reporting Bugs

If you find a bug, please create an issue with:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- System information (OS, Python version, etc.)
- Error messages and logs

### Suggesting Features

Feature suggestions are welcome! Please:

- Check if the feature already exists or is planned
- Provide a clear use case
- Explain why it would benefit the project
- Consider implementation complexity

### Pull Requests

1. **Fork and Clone**
   ```bash
   git clone https://github.com/maidulcu/smart-ai-scraper.git
   cd smart-ai-scraper
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set Up Development Environment**
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   pip install -e .
   playwright install chromium
   python -m spacy download en_core_web_sm
   ```

4. **Make Your Changes**
   - Write clean, readable code
   - Follow PEP 8 style guidelines
   - Add docstrings to functions and classes
   - Update documentation if needed

5. **Add Tests**
   ```bash
   # Add tests in tests/ directory
   pytest tests/
   ```

6. **Format Code**
   ```bash
   black smart_ai_scraper/
   flake8 smart_ai_scraper/
   mypy smart_ai_scraper/
   ```

7. **Commit Changes**
   ```bash
   git add .
   git commit -m "Add feature: your feature description"
   ```

8. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

## Development Guidelines

### Code Style

- Follow PEP 8
- Use type hints where appropriate
- Write descriptive variable and function names
- Keep functions focused and small
- Add docstrings (Google style)

Example:
```python
def scrape_url(url: str, extractor_type: str = "general") -> Dict[str, Any]:
    """
    Scrape a URL and extract data.

    Args:
        url: The URL to scrape
        extractor_type: Type of extraction to perform

    Returns:
        Dictionary containing scraped data

    Raises:
        ValueError: If URL is invalid
    """
    pass
```

### Testing

- Write unit tests for new features
- Ensure existing tests pass
- Aim for high test coverage
- Use pytest fixtures for setup/teardown

### Documentation

- Update README.md for new features
- Add docstrings to all public functions
- Include usage examples
- Update configuration documentation

### Commit Messages

Use clear, descriptive commit messages:

```
Add feature: AI-powered CAPTCHA solving

- Implement image recognition for CAPTCHAs
- Add configuration options
- Update documentation
```

## Project Structure

```
smart-ai-scraper/
├── smart_ai_scraper/     # Main package
│   ├── core/             # Core functionality
│   ├── extractors/       # Data extraction
│   ├── utils/            # Utilities
│   ├── storage/          # Storage backends
│   ├── tasks/            # Celery tasks
│   └── cli.py            # CLI interface
├── examples/             # Usage examples
├── tests/                # Test suite
└── docs/                 # Documentation
```

## Areas for Contribution

### High Priority

- Additional extractors (social media, job listings, etc.)
- Performance optimizations
- Test coverage improvements
- Documentation enhancements

### Medium Priority

- Cloud deployment guides
- Web UI for scraper management
- More AI model integrations
- Proxy rotation improvements

### Low Priority

- Additional browser support
- Alternative storage backends
- Monitoring and alerting
- API server mode

## Testing Locally

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=smart_ai_scraper

# Run specific test file
pytest tests/test_scraper.py

# Run with verbose output
pytest -v
```

## Getting Help

- Create an issue for questions
- Join our community discussions
- Check existing issues and PRs
- Review documentation

## Recognition

Contributors will be:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in relevant documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing to Smart AI Scraper!
