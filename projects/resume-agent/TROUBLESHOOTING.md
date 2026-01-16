# 🔧 Troubleshooting Guide

## Web Scraping Issues

### Problem: "Could not extract sufficient text from URL"

This usually happens when:
1. The website uses JavaScript to load content dynamically
2. The website has anti-scraping measures
3. The website requires authentication

### Solutions:

#### Option 1: Install Selenium (Recommended for JavaScript-rendered pages)

```bash
pip install selenium
```

You'll also need Chrome/Chromium installed on your system. The scraper will automatically use Selenium if available.

**macOS:**
```bash
brew install chromedriver
```

**Linux:**
```bash
sudo apt-get install chromium-chromedriver
# or
sudo yum install chromium-chromedriver
```

**Windows:**
Download ChromeDriver from: https://chromedriver.chromium.org/

#### Option 2: Use a Text File Instead

If scraping continues to fail, you can manually copy the job description:

1. Open the job posting in your browser
2. Copy all the text
3. Save it to a file (e.g., `job_description.txt`)
4. Run:
   ```bash
   python -m src.cli job_description.txt
   ```

#### Option 3: Disable Selenium

If Selenium is causing issues, you can disable it:
```bash
python -m src.cli <url> --no-selenium
```

### Testing the Scraper

You can test if a URL is scrapable by checking the response:

```python
from src.utils.web_scraper import scrape_job_description

try:
    text = scrape_job_description("https://your-url-here")
    print(f"Success! Extracted {len(text)} characters")
    print(text[:500])  # First 500 chars
except Exception as e:
    print(f"Failed: {e}")
```

## Common Errors

### "OPENAI_API_KEY environment variable is required"
- Make sure you have a `.env` file in the project root
- Check that `OPENAI_API_KEY=your_key_here` is set

### "Resume index file not found"
- Create `src/data/resumes/resume_index.json`
- Make sure the path is correct

### "Resume PDF not found"
- Check that your PDF exists at the path in `resume_index.json`
- Use absolute paths if relative paths don't work

### Rate Limit Errors
- The scraper will automatically retry with exponential backoff
- Consider using a model with higher rate limits
- Wait a few minutes and try again

## Getting Help

If you continue to have issues:
1. Run with `--verbose` flag to see detailed logs
2. Check the error message for specific guidance
3. Try the file-based approach as a workaround
