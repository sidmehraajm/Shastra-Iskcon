#!/usr/bin/env python3
import os
import sys

def get_title(filepath):
    """
    Try to extract a title from the markdown file by looking for a first-level heading.
    If not found, return the filename (without extension).
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                # Look for a line starting with "# " (an H1 heading)
                if line.startswith("# "):
                    return line.strip("# ").strip()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
    # Fallback: use filename without extension
    return os.path.splitext(os.path.basename(filepath))[0]

def generate_summary(root_dir, rel_path=""):
    """
    Recursively scan the directory at root_dir/rel_path.
    Return a list of lines formatted as GitBook SUMMARY entries.
    """
    current_dir = os.path.join(root_dir, rel_path)
    try:
        items = sorted(os.listdir(current_dir), key=lambda s: s.lower())
    except Exception as e:
        print(f"Error listing directory {current_dir}: {e}")
        return []

    entries = []
    
    # Process directories first (ignoring common unwanted directories)
    for item in items:
        full_path = os.path.join(current_dir, item)
        if os.path.isdir(full_path) and item not in ['node_modules', '.git']:
            # If directory has a README.md, use that as the entry title
            readme_path = os.path.join(full_path, "README.md")
            if os.path.exists(readme_path):
                title = get_title(readme_path)
                link = os.path.join(rel_path, item, "README.md").replace(os.sep, '/')
                entries.append((item, title, link, True))
            else:
                # Otherwise, use the directory name
                entries.append((item, item, None, True))
    
    # Process markdown files in the current directory (excluding SUMMARY.md and README.md)
    for item in items:
        full_path = os.path.join(current_dir, item)
        if os.path.isfile(full_path) and item.endswith(".md") and item not in ["SUMMARY.md", "README.md"]:
            title = get_title(full_path)
            link = os.path.join(rel_path, item).replace(os.sep, '/')
            entries.append((item, title, link, False))
    
    summary_lines = []
    # Determine the indentation based on directory depth
    base_depth = rel_path.count(os.sep) if rel_path else 0

    for item, title, link, is_dir in entries:
        # Compute current depth: add one level for this item
        current_depth = base_depth + 1
        indent = "  " * (current_depth - 1)
        if link:
            summary_lines.append(f"{indent}* [{title}]({link})")
        else:
            # If no link (for directories without README), just list the directory name
            summary_lines.append(f"{indent}* {title}")
        
        # For directories, recursively generate sub-entries.
        if is_dir:
            sub_rel_path = os.path.join(rel_path, item) if rel_path else item
            sub_lines = generate_summary(root_dir, sub_rel_path)
            summary_lines.extend(sub_lines)
    
    return summary_lines

def main():
    # Use the current directory or prompt for a folder
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = input("Enter the folder path (default is current directory): ").strip() or "."
    
    root_dir = os.path.abspath(root_dir)  # Convert to absolute path
    
    # Build the SUMMARY file contents
    summary_content = ["# Table of contents", ""]
    summary_content.extend(generate_summary(root_dir))
    summary_text = "\n".join(summary_content)
    
    # Write to SUMMARY.md in the root directory
    output_file = os.path.join(root_dir, "SUMMARY.md")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(summary_text)
        print(f"SUMMARY.md generated successfully at: {output_file}")
    except Exception as e:
        print(f"Error writing SUMMARY.md: {e}")

if __name__ == "__main__":
    main()
