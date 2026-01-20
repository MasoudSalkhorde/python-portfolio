"""Web scraping utilities for job descriptions."""
import logging
import re
import json
import time
from typing import Optional
import requests
from bs4 import BeautifulSoup
from src.utils.config import Config

logger = logging.getLogger(__name__)

# Try to import Selenium for JavaScript-rendered pages (optional)
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    logger.debug("Selenium not available - JavaScript rendering disabled")

def clean_text(text: str) -> str:
    """Clean extracted text from HTML."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def scrape_with_selenium(url: str) -> Optional[str]:
    """
    Scrape using Selenium for JavaScript-rendered pages.
    
    Args:
        url: URL to scrape
        
    Returns:
        Extracted text or None if Selenium is not available or fails
    """
    if not SELENIUM_AVAILABLE:
        return None
    
    logger.info("Attempting to scrape with Selenium (JavaScript rendering)...")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')  # New headless mode
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--window-size=1920,1080')
        # Use a more realistic user agent
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.set_page_load_timeout(Config.REQUEST_TIMEOUT)
            
            logger.debug(f"Loading page: {url}")
            driver.get(url)
            
            # Wait for content to load (up to 10 seconds)
            try:
                WebDriverWait(driver, 10).until(
                    lambda d: d.execute_script('return document.readyState') == 'complete'
                )
                # Additional wait for dynamic content
                time.sleep(2)
            except TimeoutException:
                logger.warning("Page load timeout, proceeding anyway...")
            
            # Try to find job description content
            # Includes specific selectors for popular job sites
            selectors = [
                # Indeed specific
                '#jobDescriptionText',
                'div[id="jobDescriptionText"]',
                'div[class*="jobsearch-jobDescriptionText"]',
                # LinkedIn specific
                'div[class*="description__text"]',
                'div[class*="show-more-less-html"]',
                # General job sites
                'div[class*="job-description"]',
                'div[class*="jobDescription"]',
                'div[class*="description"]',
                'div[class*="content"]',
                'section[class*="description"]',
                'article[class*="description"]',
                'main',
                'article',
            ]
            
            text = None
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        text = elements[0].text
                        if text and len(text) > 100:
                            logger.debug(f"Found content using selector: {selector}")
                            break
                except Exception:
                    continue
            
            # Fallback: get body text
            if not text or len(text) < 100:
                try:
                    body = driver.find_element(By.TAG_NAME, 'body')
                    text = body.text
                except Exception:
                    pass
            
            if text and len(text) > 50:
                text = clean_text(text)
                logger.info(f"Selenium extracted {len(text)} characters")
                return text
            else:
                logger.warning("Selenium extraction produced insufficient text")
                return None
                
        finally:
            if driver:
                driver.quit()
                
    except WebDriverException as e:
        logger.warning(f"Selenium failed: {e}")
        return None
    except Exception as e:
        logger.warning(f"Selenium error: {e}")
        return None


def get_google_doc_text(url: str) -> Optional[str]:
    """
    Extract text from Google Docs URL by using export URL.
    
    Args:
        url: Google Docs URL
        
    Returns:
        Document text or None if extraction fails
    """
    # Extract document ID from various Google Docs URL formats
    # Formats:
    # - https://docs.google.com/document/d/DOC_ID/edit
    # - https://docs.google.com/document/d/DOC_ID/edit?usp=sharing
    # - https://docs.google.com/document/d/DOC_ID
    
    doc_id_match = re.search(r'/document/d/([a-zA-Z0-9_-]+)', url)
    if not doc_id_match:
        return None
    
    doc_id = doc_id_match.group(1)
    
    # Use the export URL to get plain text
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    
    logger.info(f"Fetching Google Doc as text: {doc_id}")
    
    try:
        headers = {
            'User-Agent': Config.USER_AGENT,
        }
        
        response = requests.get(
            export_url,
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            allow_redirects=True
        )
        
        if response.status_code == 200:
            text = response.text.strip()
            if len(text) > 50:
                logger.info(f"Extracted {len(text)} characters from Google Doc")
                return text
        
        logger.warning(f"Google Doc export failed with status {response.status_code}")
        return None
        
    except Exception as e:
        logger.warning(f"Failed to fetch Google Doc: {e}")
        return None


def scrape_job_description(url: str, use_selenium: bool = True) -> str:
    """
    Scrape job description from a URL.
    
    Args:
        url: URL of the job posting
        use_selenium: Whether to try Selenium if initial scraping fails
        
    Returns:
        Extracted job description text
        
    Raises:
        ValueError: If URL is invalid or scraping fails
        requests.RequestException: If HTTP request fails
    """
    logger.info(f"Scraping job description from: {url}")
    
    # Special handling for Google Docs
    if 'docs.google.com/document' in url:
        text = get_google_doc_text(url)
        if text and len(text) > 50:
            return text
        logger.warning("Google Doc export failed, trying standard scraping...")
    
    # First, try standard requests + BeautifulSoup
    try:
        headers = {
            'User-Agent': Config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/',
        }
        
        response = requests.get(
            url,
            headers=headers,
            timeout=Config.REQUEST_TIMEOUT,
            allow_redirects=True
        )
        response.raise_for_status()
        
        # Check if response is JSON (some APIs return JSON)
        content_type = response.headers.get('Content-Type', '').lower()
        if 'application/json' in content_type:
            try:
                data = response.json()
                # Try to extract text from JSON
                text = json.dumps(data, indent=2)
                if len(text) > 100:
                    logger.info("Extracted content from JSON response")
                    return text
            except json.JSONDecodeError:
                pass
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer", "aside"]):
            script.decompose()
        
        # Try to find main content area (common patterns)
        main_content = None
        
        # Expanded list of selectors
        selectors = [
            'div[class*="job-description"]',
            'div[class*="jobDescription"]',
            'div[class*="description"]',
            'div[class*="content"]',
            'div[class*="job-content"]',
            'div[class*="posting"]',
            'section[class*="description"]',
            'article[class*="description"]',
            'div[data-testid*="description"]',
            'div[id*="description"]',
            'main',
            'article',
            '[role="main"]',
            '[role="article"]',
        ]
        
        for selector in selectors:
            try:
                main_content = soup.select_one(selector)
                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                    if text and len(text) > 100:
                        logger.debug(f"Found content using selector: {selector}")
                        break
            except Exception:
                continue
        
        # If no specific selector works, try to get body text
        if not main_content:
            main_content = soup.find('body') or soup
        
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        text = clean_text(text)
        
        # More aggressive fallback: get all text from common content tags
        if not text or len(text) < 100:
            logger.warning("Extracted text seems too short, trying aggressive extraction")
            # Try getting text from all paragraphs, divs, and list items
            paragraphs = soup.find_all(['p', 'div', 'li', 'span', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            text_parts = []
            seen_texts = set()  # Avoid duplicates
            
            for p in paragraphs:
                p_text = clean_text(p.get_text())
                if p_text and len(p_text) > 10 and p_text not in seen_texts:
                    text_parts.append(p_text)
                    seen_texts.add(p_text)
            
            text = '\n'.join(text_parts)
            text = clean_text(text)
        
        # If still insufficient and Selenium is available, try it
        if (not text or len(text) < 50) and use_selenium and SELENIUM_AVAILABLE:
            logger.info("Standard scraping failed, trying Selenium for JavaScript-rendered content...")
            selenium_text = scrape_with_selenium(url)
            if selenium_text and len(selenium_text) > 50:
                return selenium_text
        
        if not text or len(text) < 50:
            # Provide helpful error message
            error_msg = (
                f"Could not extract sufficient text from URL. Extracted {len(text)} characters.\n"
                f"This might be because:\n"
                f"  1. The page uses JavaScript to load content (try installing Selenium: pip install selenium)\n"
                f"  2. The page requires authentication\n"
                f"  3. The page has anti-scraping measures\n\n"
                f"Alternative: Save the job description to a text file and use:\n"
                f"  python -m src.cli job_description.txt"
            )
            raise ValueError(error_msg)
        
        logger.info(f"Successfully extracted {len(text)} characters from job description")
        return text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"HTTP request failed: {e}")
        
        # If we got a 403 Forbidden, try Selenium as a fallback
        if '403' in str(e) and use_selenium and SELENIUM_AVAILABLE:
            logger.info("Got 403 Forbidden, trying Selenium to bypass anti-scraping...")
            selenium_text = scrape_with_selenium(url)
            if selenium_text and len(selenium_text) > 50:
                return selenium_text
        
        raise ValueError(f"Failed to fetch URL: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during scraping: {e}")
        raise ValueError(f"Failed to scrape job description: {e}") from e

def is_url(text: str) -> bool:
    """Check if a string is a valid URL."""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return bool(url_pattern.match(text))
