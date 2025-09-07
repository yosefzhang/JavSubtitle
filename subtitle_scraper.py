#!/usr/bin/env python3
"""
Subtitle scraper for subtitlecat.com

This script provides a command-line interface to search for subtitles on subtitlecat.com 
and download Chinese subtitles (Simplified or Traditional) when available.

Usage:
python3 subtitle_scraper.py <keyword|filename|folder>
Example: python3 subtitle_scraper.py NIMA-014
Example: python3 subtitle_scraper.py "/path/to/NIMA-014.mp4"
Example: python3 subtitle_scraper.py "/path/to/videos/"
"""

import sys
import os
import requests
import re
import argparse
from subtitlecat import search_subtitlecat, get_subtitle_page_content

def extract_keyword(input_arg):
    """
    Extract the keyword (番号) from the input argument.
    Handles both direct keywords and file paths.
    """
    try:
        # First, try to treat it as a file path and extract the filename
        filename = os.path.splitext(os.path.basename(input_arg))[0]
        
        # Extract the番号 which typically follows the pattern: letters-hyphen-numbers
        # This pattern matches identifiers like "NIMA-014", "ABCD-123", etc.
        # The pattern should be strict: at least one letter, followed by a hyphen, followed by at least one digit
        match = re.match(r'^([A-Za-z]+-\d+)', input_arg)
        if match:
            return match.group(1)
        else:
            # Try the same strict pattern on the filename
            match = re.match(r'^([A-Za-z]+-\d+)', filename)
            if match:
                return match.group(1)
            else:
                # If no pattern match, return None to indicate we couldn't extract a keyword
                return None
    except Exception as e:
        # If any error occurs, return None
        return None

def is_video_file(filename):
    """
    Check if a file is a video file based on its extension
    """
    video_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.ts'}
    _, ext = os.path.splitext(filename)
    return ext.lower() in video_extensions

def is_hidden_file(filepath):
    """
    Check if a file is hidden on either Unix-like systems or Windows
    """
    name = os.path.basename(filepath)
    
    # For Unix-like systems (files starting with .)
    if name.startswith('.'):
        return True
    
    # For Windows (files with hidden attribute)
    try:
        import stat
        file_stat = os.stat(filepath)
        return bool(file_stat.st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN)
    except (AttributeError, OSError):
        # If we can't check Windows attributes, just return False
        return False

def is_subtitle_exists(keyword, download_folder):
    """
    Check if a subtitle file with the given keyword already exists in the download folder
    Looks for both .zh-CN.srt and .zh-TW.srt files
    """
    # Possible subtitle filenames
    subtitle_files = [
        f"{keyword}.zh-CN.srt",
        f"{keyword}.zh-TW.srt",
        f"{keyword}.srt"
    ]
    
    # Check each possible subtitle file
    for subtitle_file in subtitle_files:
        full_path = os.path.join(download_folder, subtitle_file)
        if os.path.exists(full_path):
            return True, full_path
    
    return False, None

def process_video_file(video_path, download_folder):
    """
    Process a single video file to find and download subtitles
    """
    print(f"Processing video file: {video_path}")
    
    # Extract keyword from the video filename
    keyword = extract_keyword(video_path)
    if not keyword:
        print(f"Could not extract keyword from {video_path}")
        return False
    
    # Check if subtitle already exists
    exists, existing_file = is_subtitle_exists(keyword, download_folder)
    if exists:
        print(f"Subtitle file already exists: {existing_file}, skipping...")
        return True
    
    print(f"Using keyword for search: {keyword}")
    
    # Use the filename without extension for .srt naming
    filename_for_srt = os.path.splitext(os.path.basename(video_path))[0]
    
    print(f"Searching for: {keyword}")
    
    result = search_subtitlecat(keyword)
    
    if result:
        print(f"Page Title: {result['page_title']}")
        print(f"Status Code: {result['status_code']}")
        print(f"Search URL: {result['url']}")
        print(f"\nFound {len(result['results'])} results:")
        if result['results']:
            for i, item in enumerate(result['results'], 1):
                print(f"{i}. {item['title']}")
                print(f"   Language: {item['language']}")
                print(f"   URL: {item['url']}\n")
                
                # Use the function to fetch the content
                print("Fetching content of the result page using get_subtitle_page_content...")
                page_content = get_subtitle_page_content(item['url'])
                if page_content and "error" not in page_content:
                    print(f"Result Page Title: {page_content['page_title']}")
                    print(f"Status: {page_content['status']}")
                    
                    # Display Chinese download information
                    chinese_info = page_content.get('chinese_downloads', {})
                    if chinese_info:
                        print(f"Chinese Simplified Available: {chinese_info.get('chinese_simplified', False)}")
                        print(f"Chinese Traditional Available: {chinese_info.get('chinese_traditional', False)}")
                        if chinese_info.get('download_links'):
                            print("Chinese Download Links:")
                            for lang, link in chinese_info['download_links'].items():
                                print(f"  {lang}: {link}")
                            
                            # Download Chinese subtitle - now using filename_for_srt instead of keyword
                            # Pass the download_folder parameter
                            download_url, language, full_path = download_chinese_subtitle(chinese_info, filename_for_srt, download_folder)
                            if download_url:  # download_url
                                print(f"\nDownloading {language} subtitle...")
                                print(f"Download URL: {download_url}")
                                
                                # Actually download the file
                                success, message = download_subtitle_file(download_url, full_path)
                                if success:
                                    print(f"✅ {message}")
                                else:
                                    print(f"❌ {message}")
                            else:
                                print("\nNo Chinese subtitle available for download")
                        else:
                            print("No Chinese download links found")
                    else:
                        print("No Chinese downloads available")
                else:
                    error_msg = page_content.get('error', 'Unknown error') if page_content else 'No content returned'
                    print(f"Error fetching result page content: {error_msg}")
        else:
            print("No results found.")
    else:
        print("Failed to retrieve search results.")
    return True

def download_chinese_subtitle(chinese_info, filename_for_srt, download_folder="."):
    """
    Download Chinese subtitle (zh-CN if available, otherwise zh-TW)
    """
    download_links = chinese_info.get('download_links', {})
    
    # Prefer zh-CN if available, otherwise use zh-TW
    if 'zh-CN' in download_links:
        download_url = download_links['zh-CN']
        language = 'Chinese Simplified (zh-CN)'
        filename = f"{filename_for_srt}.zh-CN.srt"  # Use the original filename for .srt naming
    elif 'zh-TW' in download_links:
        download_url = download_links['zh-TW']
        language = 'Chinese Traditional (zh-TW)'
        filename = f"{filename_for_srt}.zh-TW.srt"
    else:
        return None, None, None
    
    # Create full path with download folder
    full_path = os.path.join(download_folder, filename)
    
    return download_url, language, full_path

def download_subtitle_file(url, full_path):
    """
    Download the subtitle file from the given URL to the specified path
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Create download folder if it doesn't exist
    download_folder = os.path.dirname(full_path)
    if not os.path.exists(download_folder):
        try:
            os.makedirs(download_folder)
            print(f"Created download folder: {download_folder}")
        except Exception as e:
            return False, f"Error creating download folder {download_folder}: {e}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        # Save the file
        with open(full_path, 'wb') as f:
            f.write(response.content)
        
        return True, f"Subtitle downloaded successfully as {full_path}"
    except requests.exceptions.RequestException as e:
        return False, f"Error downloading subtitle: {e}"
    except Exception as e:
        return False, f"Error saving subtitle: {e}"

def main():
    """
    Main function to search for subtitles on subtitlecat.com
    Usage: python3 subtitle_scraper.py <keyword|filename|folder>
    Example: python3 subtitle_scraper.py NIMA-014
    Example: python3 subtitle_scraper.py "/path/to/NIMA-014.mp4"
    Example: python3 subtitle_scraper.py "/path/to/videos/"
    """
    # Create argument parser
    parser = argparse.ArgumentParser(description="Subtitle scraper for subtitlecat.com")
    parser.add_argument("input", help="Keyword, filename, or folder path to search for subtitles")
    parser.add_argument("--output-dir", "-o", default=None, 
                        help="Output directory for downloaded subtitles (default: current directory, input file's directory, or input folder)")
    
    # Parse arguments
    args = parser.parse_args()
    input_arg = args.input
    download_folder = args.output_dir
    
    # Check if input is a folder
    if os.path.isdir(input_arg):
        print(f"Input is a folder: {input_arg}")
        # If no output directory specified, use the input folder as output directory
        if download_folder is None:
            download_folder = input_arg
            print(f"Using input folder as output directory: {download_folder}")
        else:
            print(f"Using specified output directory: {os.path.abspath(download_folder)}")
        
        # Process all video files in the folder that have extractable keywords
        video_files_processed = 0
        video_files_with_keywords = 0
        for filename in os.listdir(input_arg):
            file_path = os.path.join(input_arg, filename)
            # Skip hidden files
            if is_hidden_file(file_path):
                continue
            if os.path.isfile(file_path) and is_video_file(filename):
                video_files_processed += 1
                # Check if we can extract a keyword from this video file
                keyword = extract_keyword(file_path)
                if keyword:
                    # Check if subtitle already exists before processing
                    exists, existing_file = is_subtitle_exists(keyword, download_folder)
                    if exists:
                        print(f"Subtitle file already exists for '{keyword}': {existing_file}, skipping...")
                        continue
                    
                    print(f"Found keyword '{keyword}' in '{filename}'")
                    video_files_with_keywords += 1
                    process_video_file(file_path, download_folder)
                    print("-" * 50)  # Separator between files
                else:
                    print(f"No valid keyword found in '{filename}', skipping...")
        
        if video_files_processed == 0:
            print("No video files found in the folder.")
        else:
            print(f"Found {video_files_processed} video files, processed {video_files_with_keywords} files with extractable keywords.")
    elif os.path.isfile(input_arg):
        # Existing file handling logic
        # If no output directory specified and input is an existing file, use its directory
        if download_folder is None:
            download_folder = os.path.dirname(os.path.abspath(input_arg))
            print(f"Using input file's directory as output folder: {download_folder}")
        else:
            print(f"Using specified output directory: {os.path.abspath(download_folder)}")
        
        # Process the single video file
        process_video_file(input_arg, download_folder)
    else:
        # Existing keyword handling logic
        if download_folder is None:
            download_folder = "."
            print(f"Using current directory as output folder: {os.path.abspath(download_folder)}")
        else:
            print(f"Using specified output directory: {os.path.abspath(download_folder)}")
        
        # Variables to track both keyword (for search) and filename (for .srt naming)
        keyword = None
        filename_for_srt = None
        
        # Extract keyword from input argument for search (don't check if it's a file)
        # Use strict pattern matching for keyword extraction
        keyword = extract_keyword(input_arg)
        
        if not keyword:
            print(f"Could not extract valid keyword from input: {input_arg}")
            return
            
        print(f"Using keyword for search: {keyword}")
        # Use the input argument as filename for .srt naming
        filename_for_srt = input_arg
        
        print(f"Searching for: {keyword}")
        
        result = search_subtitlecat(keyword)
        
        if result:
            print(f"Page Title: {result['page_title']}")
            print(f"Status Code: {result['status_code']}")
            print(f"Search URL: {result['url']}")
            print(f"\nFound {len(result['results'])} results:")
            if result['results']:
                for i, item in enumerate(result['results'], 1):
                    print(f"{i}. {item['title']}")
                    print(f"   Language: {item['language']}")
                    print(f"   URL: {item['url']}\n")
                    
                    # Use the function to fetch the content
                    print("Fetching content of the result page using get_subtitle_page_content...")
                    page_content = get_subtitle_page_content(item['url'])
                    if page_content and "error" not in page_content:
                        print(f"Result Page Title: {page_content['page_title']}")
                        print(f"Status: {page_content['status']}")
                        
                        # Display Chinese download information
                        chinese_info = page_content.get('chinese_downloads', {})
                        if chinese_info:
                            print(f"Chinese Simplified Available: {chinese_info.get('chinese_simplified', False)}")
                            print(f"Chinese Traditional Available: {chinese_info.get('chinese_traditional', False)}")
                            if chinese_info.get('download_links'):
                                print("Chinese Download Links:")
                                for lang, link in chinese_info['download_links'].items():
                                    print(f"  {lang}: {link}")
                                
                                # Download Chinese subtitle - now using filename_for_srt instead of keyword
                                # Pass the download_folder parameter
                                download_url, language, full_path = download_chinese_subtitle(chinese_info, filename_for_srt, download_folder)
                                if download_url:  # download_url
                                    print(f"\nDownloading {language} subtitle...")
                                    print(f"Download URL: {download_url}")
                                    
                                    # Actually download the file
                                    success, message = download_subtitle_file(download_url, full_path)
                                    if success:
                                        print(f"✅ {message}")
                                    else:
                                        print(f"❌ {message}")
                                else:
                                    print("\nNo Chinese subtitle available for download")
                            else:
                                print("No Chinese download links found")
                        else:
                            print("No Chinese downloads available")
                    else:
                        error_msg = page_content.get('error', 'Unknown error') if page_content else 'No content returned'
                        print(f"Error fetching result page content: {error_msg}")
            else:
                print("No results found.")
        else:
            print("Failed to retrieve search results.")

if __name__ == "__main__":
    main()