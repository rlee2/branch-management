#!/usr/bin/env python3
"""
Script to fetch Jenkins version information for repositories listed in repos-release.txt.

Usage:
    python get_jenkins_versions.py          # Fetch versions (you must be logged in already)
    python get_jenkins_versions.py --login  # Open browser to log in to Jenkins first

Prerequisites:
    pip install selenium
"""

import os
import sys
import re
import time
import argparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Configuration
JENKINS_BASE_URL = "https://jenkins.dev.hk.privemanagers.com"
JENKINS_VIEW_PATH = "/view/Prive%20Micro/job"
REPO_FILE = "repos-release.txt"
PROFILE_DIR = os.path.expanduser("~/.config/jenkins-chrome-profile")


def load_repos(file_path):
    """Load repositories from file, skipping comments and empty lines."""
    repos = []
    if not os.path.exists(file_path):
        return repos
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                repos.append(line)
    return repos


def create_chrome_driver():
    """Create a Chrome driver instance with a dedicated persistent profile."""
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Use a dedicated persistent profile for this script
    chrome_options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    
    try:
        driver = webdriver.Chrome(options=chrome_options)
        print(f"✅ Launched Chrome browser")
        print(f"   Profile: {PROFILE_DIR}")
        return driver
    except Exception as e:
        print(f"❌ Failed to launch Chrome: {e}")
        sys.exit(1)


def login_mode(driver):
    """Open Jenkins for the user to log in manually."""
    print("\n🔐 LOGIN MODE")
    print("=" * 60)
    print(f"Opening Jenkins at: {JENKINS_BASE_URL}")
    print("Please log in manually, then press Enter when done...")
    print("=" * 60)
    
    driver.get(JENKINS_BASE_URL)
    input("\n>>> Press Enter after you have logged in... ")
    print("✅ Login complete! Your session is now saved.")
    print("   Next time, run without --login to fetch versions.")


def get_latest_build_info(driver, repo_name):
    """
    Navigate to Jenkins job page, find the latest build number and check Push Docker status.
    Returns (build_number, docker_success_bool) or (None, False).
    """
    url = f"{JENKINS_BASE_URL}{JENKINS_VIEW_PATH}/{repo_name}/job/master/"
    
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(5)  # Wait for Stage View to load
        
        page_source = driver.page_source
        
        # Check if we're on a login page
        if "login" in page_source.lower() and "password" in page_source.lower():
            print(f"  ⚠️ Jenkins requires login! Run with --login first")
            return None, False
        
        # 1. Find the latest build number from the page
        # Look for build links in Jenkins format
        build_link_pattern = rf'/job/{repo_name}/job/master/(\d+)/'
        build_numbers = re.findall(build_link_pattern, page_source)
        
        if not build_numbers:
            build_numbers = re.findall(r'href=["\'](\d+)/["\']', page_source)
        
        if not build_numbers:
            return None, False
            
        latest_build = max(int(num) for num in build_numbers)
        build_str = str(latest_build)
        
        # 2. Check Push Docker status
        docker_success = True # Default to true if we can't find the info
        headers = driver.find_elements(By.CSS_SELECTOR, "th.stage-header-name-")
        if not headers:
            headers = driver.find_elements(By.TAG_NAME, "th")
            
        push_docker_idx = -1
        for i, h in enumerate(headers):
            if "Push Docker" in h.text:
                push_docker_idx = i
                break
        
        if push_docker_idx != -1:
            rows = driver.find_elements(By.CSS_SELECTOR, "tr.job-row")
            if not rows:
                rows = driver.find_elements(By.TAG_NAME, "tr")
            
            target_row = None
            for row in rows:
                if f"#{build_str}" in row.text:
                    target_row = row
                    break
            
            if target_row:
                cells = target_row.find_elements(By.TAG_NAME, "td")
                if len(cells) > push_docker_idx:
                    cell = cells[push_docker_idx]
                    classes = cell.get_attribute('class') or ""
                    
                    # Log the status found
                    if "SUCCESS" in classes:
                        print(f"  🐳 Push Docker: SUCCESS")
                        docker_success = True
                    else:
                        docker_success = False
                        # Try to extract a clean status name if possible (e.g., 'FAILED', 'IN_PROGRESS')
                        status = "NOT SUCCESSFUL"
                        for s in ["FAILED", "IN_PROGRESS", "ABORTED", "UNSTABLE"]:
                            if s in classes:
                                status = s
                                break
                        print(f"  🐳 Push Docker: {status} (Class: {classes})")
                else:
                    print(f"  ⚠️ Could not find stage cell for Push Docker")
        
        return build_str, docker_success

    except Exception as e:
        print(f"  ⚠️ Error getting build info for {repo_name}: {e}")
        return None, False


def get_release_version(driver, repo_name, build_number):
    """
    Navigate to the specific build page and extract the release version.
    Looks for text like "Version 2026-02-06.master-15" and extracts "2026-02-06.master-15".
    """
    url = f"{JENKINS_BASE_URL}{JENKINS_VIEW_PATH}/{repo_name}/job/master/{build_number}/"
    
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(3)  # Wait for dynamic content
        
        page_source = driver.page_source
        
        # Look for "Version X.X.X" pattern
        version_match = re.search(r'Version\s+(\d{4}-\d{2}-\d{2}\.[a-zA-Z0-9_-]+)', page_source)
        
        if version_match:
            return version_match.group(1)
        
        # Alternative pattern
        alt_match = re.search(r'(\d{4}-\d{2}-\d{2}\.master-\d+)', page_source)
        if alt_match:
            return alt_match.group(1)
        
        return None
    except TimeoutException:
        print(f"  ⚠️ Timeout loading build page for {repo_name} #{build_number}")
        return None
    except WebDriverException as e:
        print(f"  ⚠️ Browser error: {str(e)[:100]}")
        return None
    except Exception as e:
        print(f"  ⚠️ Error getting release version for {repo_name}: {e}")
        return None


def main():
    """Main function to fetch Jenkins versions for all repositories."""
    parser = argparse.ArgumentParser(description="Fetch Jenkins version information")
    parser.add_argument("--login", action="store_true", 
                        help="Open browser to log in to Jenkins first")
    args = parser.parse_args()
    
    # Get the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_file_path = os.path.join(script_dir, REPO_FILE)
    
    # Load repositories
    repos = load_repos(repo_file_path)
    
    if not repos and not args.login:
        print(f"⚠️ No repositories found in {REPO_FILE}")
        sys.exit(0)
    
    if not args.login:
        print(f"📋 Found {len(repos)} repositories to process\n")
    
    # Launch Chrome
    driver = create_chrome_driver()
    
    try:
        if args.login:
            login_mode(driver)
            return
        
        results = []
        
        for full_repo in repos:
            # Extract repo name (part after the slash)
            repo_name = full_repo.split('/')[-1] if '/' in full_repo else full_repo
            
            print(f"🔍 Processing: {repo_name}")
            
            # Get latest build number and Docker status
            build_number, docker_success = get_latest_build_info(driver, repo_name)
            
            if not build_number:
                print(f"  ⚠️ Could not find latest build number")
                results.append((repo_name, "N/A", True))
                continue
            
            print(f"  📦 Latest build: #{build_number}")
            
            # Get release version
            release_version = get_release_version(driver, repo_name, build_number)
            
            if release_version:
                print(f"  ✅ Release version: {release_version}")
                results.append((repo_name, release_version, docker_success))
            else:
                print(f"  ⚠️ Could not extract release version")
                results.append((repo_name, "N/A", docker_success))
            
            time.sleep(1)  # Small delay between requests
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 SUMMARY: Repository -> Release Version")
        print("=" * 60)
        
        for repo_name, version, docker_ok in results:
            warning = "" if docker_ok else " ⚠️ [Push Docker Failed!]"
            print(f"{repo_name} -> {version}{warning}")
        
        return results
    
    finally:
        driver.quit()
        print("\n📑 Closed Chrome browser")


if __name__ == "__main__":
    main()
