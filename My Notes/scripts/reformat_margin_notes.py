import re

# Path to your markdown file
input_file = "/Volumes/Krishna_SSD/Bhagwatam.txt"
output_file = "/Volumes/Krishna_SSD/Bhagwatam_mg.txt"


# Regex patterns
canto_pattern = re.compile(r"Canto (\d+) >>")
chapter_pattern = re.compile(r"Chapter (\d+) >>")
text_pattern = re.compile(r"Text (\d+):")

def create_obsidian_link(canto, chapter, text):
    """Generates an Obsidian link for a verse."""
    return f"[[SB_Verse_{canto}.{chapter}.{text}]]"

def process_bhagwatam_file(input_path, output_path):
    """Reads the input file, inserts Obsidian links, and writes to the output file."""

    canto = None
    chapter = None
    updated_lines = []

    with open(input_path, "r", encoding="utf-8") as infile:
        for line in infile:
            # Check for Canto
            canto_match = canto_pattern.search(line)
            if canto_match:
                canto = canto_match.group(1)
                updated_lines.append(line)
                continue  # Skip to the next line after updating canto

            # Check for Chapter
            chapter_match = chapter_pattern.search(line)
            if chapter_match:
                chapter = chapter_match.group(1)
                updated_lines.append(line)
                continue  # Skip to the next line after updating chapter

            # Check for Text (Verse)
            text_match = text_pattern.search(line)
            if text_match and canto and chapter:
                text_num = text_match.group(1)
                link = create_obsidian_link(canto, chapter, text_num)
                modified_line = line.replace(f"Text {text_num}:", f"{link} Text {text_num}:")
                updated_lines.append(modified_line)
            else:
                updated_lines.append(line)

    with open(output_path, "w", encoding="utf-8") as outfile:
        outfile.writelines(updated_lines)

# Run the processing
process_bhagwatam_file(input_file, output_file)

print(f"Processed file: {input_file} and created: {output_file}")