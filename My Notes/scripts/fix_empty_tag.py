import os
import re

def find_wikilinks(text):
    """
    Extract wikilinks from text.
    Handles cases with aliasing (e.g., [[Note|Alias]]) by returning only the note name.
    """
    pattern = re.compile(r'\[\[([^\]]+)\]\]')
    links = pattern.findall(text)
    # Remove any alias part (text after a | character)
    return {link.split('|')[0].strip() for link in links}

def file_exists_in_tags(tags_dir, note_name):
    """
    Check if a file named 'note_name.md' exists in the TAGS folder (case-insensitive).
    """
    target_filename = note_name.lower() + ".md"
    for file in os.listdir(tags_dir):
        if file.lower() == target_filename:
            return True
    return False

def create_note_file(tags_dir, note_name):
    """
    Create a new Markdown file with the given note_name in the TAGS folder.
    The file is pre-populated with a simple header.
    """
    file_path = os.path.join(tags_dir, note_name + ".md")
    with open(file_path, 'w', encoding="utf-8") as f:
        f.write(f"# {note_name}\n")
    print(f"Created file: {file_path}")

def scan_and_create(tags_dir):
    """
    Scan all Markdown files in the provided folder (including subfolders) for wikilinks.
    Prints each file it opens and the wikilinks it finds.
    For every wikilink that does not already have a corresponding file in the TAGS folder,
    a new file is created.
    """
    wikilinks = set()
    for root, dirs, files in os.walk(tags_dir):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                print(f"\nScanning file: {file_path}")
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    file_links = find_wikilinks(content)
                    print(f"  Found wikilinks: {file_links}")
                    wikilinks.update(file_links)
                except Exception as e:
                    print(f"  Error reading {file_path}: {e}")
    print(f"\nTotal unique wikilinks found: {len(wikilinks)}")

    # Create missing tag files
    for tag in wikilinks:
        if not file_exists_in_tags(tags_dir, tag):
            create_note_file(tags_dir, tag)

if __name__ == "__main__":
    tags_directory = input("Enter the path to your TAGS folder: ").strip()
    if not os.path.isdir(tags_directory):
        print("Invalid folder path. Please check the path and try again.")
    else:
        scan_and_create(tags_directory)
