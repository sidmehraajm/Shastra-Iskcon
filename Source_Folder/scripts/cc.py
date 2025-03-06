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
    """Save file asynchronously."""
    def write_to_file():
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        log_message(f"Saved: {file_path}")
    thread = threading.Thread(target=write_to_file)
    thread.start()

def extract_chapter_number(url):
    """Extracts chapter number from a CC chapter URL (…/cc/{part}/{chapter}/)."""
    m = re.search(r"/en/library/cc/[^/]+/(\d+)/$", url)
    return int(m.group(1)) if m else None

def extract_verse_identifier(url):
    """Extracts verse identifier from a CC verse URL (…/cc/{part}/{chapter}/{verse}/)."""
    m = re.search(r"/en/library/cc/[^/]+/\d+/([\d\-]+)/$", url)
    return m.group(1) if m else None

def scrape_verse_cc(driver, verse_url, part, chapter):
    """
    Loads a verse page and scrapes its content into Vedabase_CC/{Part}/Chapter_{chapter}/Verse_{verse_id}.md

    - Bengali: first tries class 'av-bengali', then fallback XPath "/html/body/div/div/div/div[2]/main/div[2]/div[2]"
    - Transliteration: tries XPath "/html/body/div/div/div/div[2]/main/div[2]/div[3]/div/div"
    - Synonyms: class 'av-synonyms'
    - Translation: class 'av-translation'
    - Purport: class 'av-purport', fallback "/html/body/div/div/div/div[3]/main/div[2]/div[6]"
    """
    driver.get(verse_url)
    try:
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
    except:
        log_message(f"Timeout loading verse page: {verse_url}")
        return

    # Extract verse title
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        title = "No Title"
    log_message(f"Scraping: {title}")

    # Folder structure
    base_folder = os.path.join("Vedabase_CC", part.capitalize(), f"Chapter_{chapter}")
    os.makedirs(base_folder, exist_ok=True)

    # Determine verse ID
    verse_id = title.split()[-1] if len(title.split()) > 1 else extract_verse_identifier(verse_url)
    if not verse_id:
        verse_id = "unknown"

    file_path = os.path.join(base_folder, f"Verse_{verse_id}.md")
    if os.path.exists(file_path):
        log_message(f"Skipping {title}, already downloaded.")
        return

    content = {}

    # 1. Bengali (try class first, fallback to XPATH)
    bengali_text = ""
    try:
        bengali_text = driver.find_element(By.CLASS_NAME, "av-bengali").text.strip()
    except:
        pass
    if not bengali_text:
        # fallback XPATH
        try:
            bengali_text = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/main/div[2]/div[2]").text.strip()
        except:
            bengali_text = ""
    content["Bengali"] = bengali_text

    # 2. Transliteration (fixed XPATH)
    try:
        translit_elem = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/main/div[2]/div[3]/div/div")
        content["Transliteration"] = translit_elem.text.strip()
    except:
        content["Transliteration"] = ""

    # 3. Synonyms & Translation (class-based)
    for sec, cls in [("Synonyms", "av-synonyms"), ("Translation", "av-translation")]:
        try:
            elem = driver.find_element(By.CLASS_NAME, cls)
            content[sec] = elem.text.strip()
        except:
            content[sec] = ""

    # 4. Purport (class-based, fallback to XPATH)
    purport_text = ""
    try:
        purport_elem = driver.find_element(By.CLASS_NAME, "av-purport")
        purport_text = purport_elem.text.strip()
    except:
        pass
    if not purport_text:
        # fallback XPATH
        try:
            purport_elem = driver.find_element(By.XPATH, "/html/body/div/div/div/div[3]/main/div[2]/div[6]")
            purport_text = purport_elem.text.strip()
        except:
            purport_text = ""
    content["Purport"] = purport_text

    # Build Markdown
    markdown_content = f"# {title}\n\n"
    for sec in ["Bengali", "Transliteration", "Synonyms", "Translation", "Purport"]:
        text = content[sec]
        if text:
            markdown_content += f"**{sec}:**\n\n{text}\n\n"

    save_verse_async(file_path, markdown_content)

def scrape_chapter_cc(driver, part, chapter):
    """Loads the chapter overview (…/cc/{part}/{chapter}/), extracts verse URLs, then scrapes each verse."""
    chapter_url = f"https://vedabase.io/en/library/cc/{part}/{chapter}/"
    log_message(f"Loading Chapter {chapter} of {part.capitalize()}: {chapter_url}")
    driver.get(chapter_url)
    time.sleep(2)

    verse_pattern = re.compile(rf"/en/library/cc/{part}/{chapter}/([\d\-]+)/$")
    links = driver.find_elements(By.TAG_NAME, "a")
    verse_urls = set()

    for link in links:
        href = link.get_attribute("href")
        if href and f"/en/library/cc/{part}/{chapter}/" in href:
            if verse_pattern.search(href):
                verse_urls.add(href)

    verse_urls = list(verse_urls)
    if not verse_urls:
        log_message(f"No verse URLs found for {part.capitalize()} Chapter {chapter}.")
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
    log_message(f"Found {len(verse_urls)} verses in {part.capitalize()} Chapter {chapter}.")
    for url in verse_urls:
        scrape_verse_cc(driver, url, part, chapter)

def scrape_part_cc(driver, part):
    """Loads the part overview (…/cc/{part}/), extracts chapter URLs, then scrapes each chapter."""
    part_url = f"https://vedabase.io/en/library/cc/{part}/"
    log_message(f"\n--- Processing {part.capitalize()} Lila: {part_url} ---")
    driver.get(part_url)
    time.sleep(3)

    chapter_pattern = re.compile(rf"/en/library/cc/{part}/(\d+)/$")
    links = driver.find_elements(By.TAG_NAME, "a")
    chapter_urls = set()

    for link in links:
        href = link.get_attribute("href")
        if href and f"/en/library/cc/{part}/" in href:
            m = chapter_pattern.search(href)
            if m:
                chapter_urls.add(href)

    chapter_urls = list(chapter_urls)
    if not chapter_urls:
        log_message(f"No chapter URLs found for {part.capitalize()} Lila.")
        return

    # Sort by numeric chapter number
    def chapter_key(url):
        m = chapter_pattern.search(url)
        if m:
            try:
                return int(m.group(1))
            except:
                return 0
        return 0

    chapter_urls.sort(key=chapter_key)
    log_message(f"Found {len(chapter_urls)} chapters in {part.capitalize()} Lila.")
    for url in chapter_urls:
        m = chapter_pattern.search(url)
        if m:
            chapter_num = int(m.group(1))
            scrape_chapter_cc(driver, part, chapter_num)

def scrape_vedabase_cc():
    """
    Scrapes all three parts of the Chaitanya Charitamrita (adi, madhya, antya),
    capturing Bengali with a fallback approach:
      - class 'av-bengali' first
      - fallback /html/body/div/div/div/div[2]/main/div[2]/div[2]
    """
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    os.makedirs("Vedabase_CC", exist_ok=True)
    parts = ["antya"]

    # parts = ["adi", "madhya", "antya"]
    for part in parts:
        scrape_part_cc(driver, part)

    driver.quit()
    log_message("Scraping completed for all parts of Chaitanya Charitamrita.")

if __name__ == "__main__":
    scrape_vedabase_cc()
