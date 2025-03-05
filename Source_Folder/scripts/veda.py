import time
import os
import threading
import re
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def log_message(message):
    """Append a message to the log file and print it."""
    with open("scraper_log.txt", "a", encoding="utf-8") as f:
        f.write(message + "\n")
    print(message)

def save_verse_async(file_path, markdown_content):
    """Save file in a separate thread."""
    def write_to_file():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        log_message(f"Saved: {file_path}")
    thread = threading.Thread(target=write_to_file)
    thread.start()

def extract_chapter_from_url(url):
    """Extracts chapter number from URL in the format .../bg/{chapter}/{verse}/"""
    try:
        parts = url.strip("/").split("/")
        # Expected parts: ["en", "library", "bg", "{chapter}", "{verse}"]
        return int(parts[3])
    except Exception:
        return None

def scrape_verse(driver, verse_url, chapter):
    """Loads a verse page and scrapes its content."""
    driver.get(verse_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except:
        log_message(f"Timeout loading verse page: {verse_url}")
        return
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        title = "No Title"
    log_message(f"Scraping: {title}")
    chapter_folder = os.path.join("Vedabase_Gita", f"Chapter_{chapter}")
    os.makedirs(chapter_folder, exist_ok=True)
    # Use the verse identifier from the title (e.g., "1.1" or "1.3-4")
    verse_identifier = title.split()[1] if len(title.split()) > 1 else "unknown"
    file_path = os.path.join(chapter_folder, f"Verse_{verse_identifier}.md")
    if os.path.exists(file_path):
        log_message(f"Skipping {title}, already downloaded.")
        return
    # Extract standard sections.
    content = {}
    sections = {"Synonyms": "av-synonyms", "Translation": "av-translation", "Purport": "av-purport"}
    for sec, cls in sections.items():
        try:
            content[sec] = driver.find_element(By.CLASS_NAME, cls).text.strip()
        except:
            content[sec] = ""
    # Extract alternate Sanskrit and Transliteration texts.
    try:
        extra_sanskrit = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/main/div[2]/div[2]/div/div").text.strip()
    except:
        extra_sanskrit = ""
    try:
        extra_translit = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/main/div[2]/div[3]/div/div").text.strip()
    except:
        extra_translit = ""
    # Assemble Markdown content.
    markdown_content = f"# {title}\n\n"
    # Place alternate Sanskrit and Transliteration immediately after the title.
    if extra_sanskrit:
        markdown_content += f"**Sanskrit (Alt):**\n\n{extra_sanskrit}\n\n"
    if extra_translit:
        markdown_content += f"**Transliteration (Alt):**\n\n{extra_translit}\n\n"
    for sec in ["Synonyms", "Translation", "Purport"]:
        if content.get(sec):
            markdown_content += f"**{sec}:**\n\n{content[sec]}\n\n"
    save_verse_async(file_path, markdown_content)

def scrape_chapter(driver, chapter):
    """Scrapes all verse URLs from the chapter overview page and processes them."""
    overview_url = f"https://vedabase.io/en/library/bg/{chapter}/"
    log_message(f"\n--- Loading Chapter {chapter} Overview: {overview_url} ---")
    driver.get(overview_url)
    time.sleep(3)  # Allow time for the page to load.
    
    # Find all <a> tags and extract verse URLs matching the pattern.
    links = driver.find_elements(By.TAG_NAME, "a")
    verse_urls = set()
    pattern = re.compile(r"/en/library/bg/" + str(chapter) + r"/([\d\-]+)/$")
    for link in links:
        href = link.get_attribute("href")
        if href and f"/en/library/bg/{chapter}/" in href:
            m = pattern.search(href)
            if m:
                verse_urls.add(href)
    verse_urls = list(verse_urls)
    if not verse_urls:
        log_message(f"No verse URLs found for Chapter {chapter}.")
        return
    # Sort verse URLs using a custom key.
    def verse_key(url):
        m = pattern.search(url)
        if m:
            identifier = m.group(1)
            if '-' in identifier:
                parts = identifier.split('-')
                try:
                    return (int(parts[0]), int(parts[1]))
                except:
                    return (int(parts[0]), 0)
            else:
                try:
                    val = int(identifier)
                    return (val, val)
                except:
                    return (0,0)
        return (0,0)
    verse_urls.sort(key=verse_key)
    log_message(f"Found {len(verse_urls)} verses for Chapter {chapter}.")
    for url in verse_urls:
        scrape_verse(driver, url, chapter)

def scrape_vedabase_overview():
    """Loops through chapters 1 to 18 using the overview page to collect verse URLs."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    main_folder = "Vedabase_Gita"
    os.makedirs(main_folder, exist_ok=True)
    for chapter in range(1, 19):
        log_message(f"\n--- Processing Chapter {chapter} ---")
        scrape_chapter(driver, chapter)
    driver.quit()
    log_message("Scraping completed for all 18 chapters.")

# Start the scraping process.
scrape_vedabase_overview()
