"""Combined scraper for subtitlecat.com

This module provides functions to search for subtitles on subtitlecat.com and 
download Chinese subtitles (Simplified or Traditional) when available.

Functions:
- search_subtitlecat: Search for subtitles by keyword
- get_subtitle_page_content: Get content of a specific subtitle page
- check_chinese_download_buttons: Check for Chinese download options
- download_chinese_subtitle: Prepare Chinese subtitle download
- download_subtitle_file: Download a subtitle file

This module is intended to be imported by other scripts that provide a user interface.
"""

import requests
from bs4 import BeautifulSoup
import urllib.parse

def search_subtitlecat(keyword):
    """
    Scrape subtitlecat.com for subtitles using a keyword search
    """
    # Validate keyword
    if not keyword or not isinstance(keyword, str):
        print("Invalid keyword provided")
        return None
    
    # URL encode the keyword
    encoded_keyword = urllib.parse.quote(keyword)
    url = f"https://www.subtitlecat.com/index.php?search={encoded_keyword}"
    
    # Set headers to mimic a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        # Send GET request
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        # Parse HTML content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        page_title = soup.title.string if soup.title else "No title found"
        
        # Extract search results
        results = []
        
        # Look for table rows that contain search results
        # Based on the website structure, results are typically in a table
        rows = soup.find_all('tr')
        
        # Convert keyword to lowercase for case-insensitive comparison
        keyword_lower = keyword.lower()
        
        for row in rows:
            # Look for links in each row
            links = row.find_all('a', href=True)
            if links:
                # Check if any link contains our keyword or seems like a subtitle link
                for link in links:
                    title = link.text.strip()
                    href = link['href']
                    # Filter for relevant results - case insensitive matching
                    if keyword_lower in title.lower() or '/view.php?' in href or '/subs/' in href:
                        # Get additional info from the row if available
                        cells = row.find_all('td')
                        language = ""
                        if len(cells) > 1:
                            language = cells[1].text.strip()
                        
                        # Handle URL properly
                        if href.startswith('/'):
                            full_url = 'https://www.subtitlecat.com' + href
                        elif href.startswith('http'):
                            full_url = href
                        else:
                            full_url = 'https://www.subtitlecat.com/' + href
                        
                        results.append({
                            'title': title,
                            'url': full_url,
                            'language': language
                        })
                        break  # Move to next row after finding a relevant link
        
        return {
            'page_title': page_title,
            'results': results,
            'url': url,
            'status_code': response.status_code
        }
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"Error parsing the webpage: {e}")
        return None

def format_subtitlecat_url(url):
    """
    Ensure we have a full URL with the subtitlecat.com domain
    """
    if url.startswith('/'):
        return 'https://www.subtitlecat.com' + url
    elif not url.startswith(('http://', 'https://')):
        return 'https://www.subtitlecat.com/' + url
    return url

def get_subtitle_page_content(url):
    """
    Fetch and return the content of a subtitle page given its URL
    """
    # Validate URL
    if not url or not isinstance(url, str):
        return {"error": "Invalid URL provided"}
    
    # Ensure we have a proper URL format
    url = format_subtitlecat_url(url)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Parse result page content
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract page title
        page_title = soup.title.string if soup.title else "No title found"
        
        # Extract text content
        content = soup.get_text(strip=True)
        
        # Check for Chinese download buttons
        chinese_download_info = check_chinese_download_buttons(soup)
        
        return {
            "url": url,
            "page_title": page_title,
            "content": content,
            "chinese_downloads": chinese_download_info,
            "status": "success"
        }
        
    except requests.exceptions.RequestException as e:
        return {"error": f"Request error: {e}"}
    except Exception as e:
        return {"error": f"Parsing error: {e}"}

def check_chinese_download_buttons(soup):
    """
    Check if the page has Chinese Simplified or Chinese Traditional download buttons
    """
    chinese_info = {
        "chinese_simplified": False,
        "chinese_traditional": False,
        "download_links": {}
    }
    
    # Look for download links with specific language codes
    download_links = soup.find_all('a', class_='green-link')
    
    for link in download_links:
        # Check if this is a download link
        if 'download' in link.get('id', '').lower() or 'download' in link.text.lower():
            # Check for Chinese Simplified (zh-CN)
            if 'zh-CN' in link.get('id', '') or 'zh-CN' in link.get('href', ''):
                chinese_info["chinese_simplified"] = True
                chinese_info["download_links"]["zh-CN"] = format_subtitlecat_url(link.get('href', ''))
            
            # Check for Chinese Traditional (zh-TW)
            if 'zh-TW' in link.get('id', '') or 'zh-TW' in link.get('href', ''):
                chinese_info["chinese_traditional"] = True
                chinese_info["download_links"]["zh-TW"] = format_subtitlecat_url(link.get('href', ''))
    
    return chinese_info

