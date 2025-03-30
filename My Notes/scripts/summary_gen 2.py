#!/usr/bin/env python3
import os
import sys
import re

total_files = 0  # Global counter to track total files processed

def get_title(filepath):
    """
    Try to extract a title from the markdown file by looking for a first-level heading.
    If not found, return the filename (without extension).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    return line.strip("# ").strip()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    return os.path.splitext(os.path.basename(filepath))[0]

def natural_sort_key(s):
    """
    Generate a natural sort key that treats numbers properly (e.g., 1, 2, 10 instead of 1, 10, 2).
    """
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def generate_summary(root_dir, rel_path=""):
    """
    Recursively scan the directory at root_dir/rel_path.
    Return a list of lines formatted as GitBook SUMMARY entries.
    """
    global total_files
    current_dir = os.path.join(root_dir, rel_path)
    try:
        items = sorted(os.listdir(current_dir), key=natural_sort_key)
    except Exception as e:
        print(f"Error listing directory {current_dir}: {e}")
        return []

    entries = []
    for item in items:
        full_path = os.path.join(current_dir, item)
        if os.path.isdir(full_path) and item not in ['node_modules', '.git']:
            readme_path = os.path.join(full_path, "README.md")
            if os.path.exists(readme_path):
                title = get_title(readme_path)
                link = os.path.join(rel_path, item, "README.md").replace(os.sep, '/')
                entries.append((item, title, link, True))
            else:
                entries.append((item, item, None, True))
    
    for item in items:
        full_path = os.path.join(current_dir, item)
        if os.path.isfile(full_path) and item.endswith(".md") and item not in ["SUMMARY.md", "README.md"]:
            title = get_title(full_path)
            link = os.path.join(rel_path, item).replace(os.sep, '/')
            entries.append((item, title, link, False))
            total_files += 1
    
    summary_lines = []
    base_depth = rel_path.count(os.sep) if rel_path else 0

    for item, title, link, is_dir in entries:
        current_depth = base_depth + 1
        indent = "  " * (current_depth - 1)
        if link:
            summary_lines.append(f"{indent}* [[{title}]]([[{link}]])")
        else:
            summary_lines.append(f"{indent}* [[{title}]]")
        
        if is_dir:
            sub_rel_path = os.path.join(rel_path, item) if rel_path else item
            sub_lines = generate_summary(root_dir, sub_rel_path)
            summary_lines.extend(sub_lines)
    
    return summary_lines

def main():
    global total_files
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = input("Enter the folder path (default is current directory): ").strip() or "."
    
    root_dir = os.path.abspath(root_dir)
    
    summary_content = ["# Table of contents", ""]
    summary_content.extend(generate_summary(root_dir))
    summary_text = "\n".join(summary_content)
    
    output_file = os.path.join(root_dir, "SUMMARY.md")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary_text)
        print(f"SUMMARY.md generated successfully at: {output_file}")
        print(f"Total files processed: {total_files}")
    except Exception as e:
        print(f"Error writing SUMMARY.md: {e}")

if __name__ == "__main__":
    main()
