import time
import os
import threading
import re
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
    """Save file asynchronously in a separate thread."""
    def write_to_file():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        log_message(f"Saved: {file_path}")
    thread = threading.Thread(target=write_to_file)
    thread.start()

def extract_by_xpath(driver, xpath):
    """Helper to extract text by XPath, or return '' if not found."""
    try:
        element = driver.find_element(By.XPATH, xpath)
        return element.text.strip()
    except:
        return ""

def extract_verse_identifier_from_url(url):
    """
    Extracts verse identifier (e.g., '1' or '3-4') from a verse URL like /en/library/sb/1/1/3/.
    Returns 'None' if not matched.
    """
    m = re.search(r"/en/library/sb/\d+/\d+/([\d\-]+)/$", url)
    return m.group(1) if m else None

def scrape_verse_sb(driver, verse_url, canto, chapter):
    """
    Loads a verse page and scrapes its content using only XPaths.
    Folder structure: Vedabase_SB/Canto_{canto}/Chapter_{chapter}/Verse_{verse_id}.md

    Final XPaths you specified:
      Sanskrit        /html/body/div/div/div/div[2]/main/div[2]/div[2]
      Transliteration /html/body/div/div/div/div[2]/main/div[2]/div[3]
      Synonyms        /html/body/div/div/div/div[2]/main/div[2]/div[4]
      Translation     /html/body/div/div/div/div[2]/main/div[2]/div[5]
      Purport         /html/body/div/div/div/div[2]/main/div[2]/div[6]
    """
    driver.get(verse_url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
    except:
        log_message(f"Timeout loading verse page: {verse_url}")
        return

    # Extract the verse title (e.g., "SB 1.1.1")
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        title = "No Title"
    log_message(f"Scraping: {title}")

    # Prepare folder structure
    base_folder = os.path.join("Vedabase_SB", f"Canto_{canto}", f"Chapter_{chapter}")
    os.makedirs(base_folder, exist_ok=True)

    # Determine verse identifier
    tokens = title.split()
    verse_id = tokens[-1] if len(tokens) > 1 else extract_verse_identifier_from_url(verse_url)
    if not verse_id:
        verse_id = "unknown"

    file_path = os.path.join(base_folder, f"Verse_{verse_id}.md")
    if os.path.exists(file_path):
        log_message(f"Skipping {title}, already downloaded.")
        return

    # Extract each section strictly by XPath
    sanskrit        = extract_by_xpath(driver, "/html/body/div/div/div/div[2]/main/div[2]/div[2]")
    transliteration = extract_by_xpath(driver, "/html/body/div/div/div/div[2]/main/div[2]/div[3]")
    synonyms        = extract_by_xpath(driver, "/html/body/div/div/div/div[2]/main/div[2]/div[4]")
    translation     = extract_by_xpath(driver, "/html/body/div/div/div/div[2]/main/div[2]/div[5]")
    purport         = extract_by_xpath(driver, "/html/body/div/div/div/div[2]/main/div[2]/div[6]")

    # Build Markdown
    markdown_content = f"# {title}\n\n"
    if sanskrit:
        markdown_content += f"**Sanskrit:**\n\n{sanskrit}\n\n"
    if transliteration:
        markdown_content += f"**Transliteration:**\n\n{transliteration}\n\n"
    if synonyms:
        markdown_content += f"**Synonyms:**\n\n{synonyms}\n\n"
    if translation:
        markdown_content += f"**Translation:**\n\n{translation}\n\n"
    if purport:
        markdown_content += f"**Purport:**\n\n{purport}\n\n"

    # Save asynchronously
    save_verse_async(file_path, markdown_content)

def scrape_chapter_sb(driver, canto, chapter):
    """
    Loads the chapter overview page and collects all verse URLs by regex.
    Then calls scrape_verse_sb() for each verse.
    """
    chapter_url = f"https://vedabase.io/en/library/sb/{canto}/{chapter}/"
    log_message(f"Loading Chapter {chapter} of Canto {canto}: {chapter_url}")
    driver.get(chapter_url)
    time.sleep(3)

    # Regex to match /en/library/sb/{canto}/{chapter}/{verse}/
    verse_pattern = re.compile(rf"/en/library/sb/{canto}/{chapter}/([\d\-]+)/$")
    links = driver.find_elements(By.TAG_NAME, "a")
    verse_urls = set()

    for link in links:
        href = link.get_attribute("href")
        if href and f"/en/library/sb/{canto}/{chapter}/" in href:
            if verse_pattern.search(href):
                verse_urls.add(href)

    verse_urls = list(verse_urls)
    if not verse_urls:
        log_message(f"No verse URLs found for Canto {canto} Chapter {chapter}.")
        return

    # Sort by numeric verse number
    def verse_key(url):
        m = verse_pattern.search(url)
        if m:
            identifier = m.group(1)
            if "-" in identifier:
                try:
                    return int(identifier.split("-")[0])
                except:
                    return 0
            else:
                try:
                    return int(identifier)
                except:
                    return 0
        return 0

    verse_urls.sort(key=verse_key)
    log_message(f"Found {len(verse_urls)} verses in Canto {canto} Chapter {chapter}.")
    for url in verse_urls:
        scrape_verse_sb(driver, url, canto, chapter)

def scrape_canto_sb(driver, canto):
    """
    Loads the canto overview page, finds all chapter URLs, then scrapes each chapter.
    """
    canto_url = f"https://vedabase.io/en/library/sb/{canto}/"
    log_message(f"\n--- Processing Canto {canto}: {canto_url} ---")
    driver.get(canto_url)
    time.sleep(3)

    chapter_pattern = re.compile(rf"/en/library/sb/{canto}/(\d+)/$")
    links = driver.find_elements(By.TAG_NAME, "a")
    chapter_urls = set()

    for link in links:
        href = link.get_attribute("href")
        if href and f"/en/library/sb/{canto}/" in href:
            m = chapter_pattern.search(href)
            if m:
                chapter_urls.add(href)

    chapter_urls = list(chapter_urls)
    if not chapter_urls:
        log_message(f"No chapter URLs found for Canto {canto}.")
        return

    # Sort chapters by numeric order
    def chapter_key(url):
        m = chapter_pattern.search(url)
        if m:
            try:
                return int(m.group(1))
            except:
                return 0
        return 0

    chapter_urls.sort(key=chapter_key)
    log_message(f"Found {len(chapter_urls)} chapters in Canto {canto}.")
    for url in chapter_urls:
        m = chapter_pattern.search(url)
        if m:
            chapter_num = int(m.group(1))
            scrape_chapter_sb(driver, canto, chapter_num)

def scrape_vedabase_sb():
    """
    Loops through all 12 cantos of SB, scraping only by the specified XPaths for each section.
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    main_folder = "Vedabase_SB"
    os.makedirs(main_folder, exist_ok=True)

    for canto in range(1, 13):
        scrape_canto_sb(driver, canto)

    driver.quit()
    log_message("Scraping completed for all 12 cantos.")

if __name__ == "__main__":
    scrape_vedabase_sb()

