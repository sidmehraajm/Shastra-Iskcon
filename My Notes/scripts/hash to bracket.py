
import re

def convert_hashtags_to_brackets(text):
    # Replace hashtags of the format #Word with [[Word]]
    return re.sub(r'(?<!\w)#(\w+)', r'[[\1]]', text)

# Read the Markdown file
with open("My Notes/Extra Notes/Margin Notes/SB 2024.md", "r", encoding="utf-8") as file:
    content = file.read()

# Convert hashtags to double brackets
converted_content = convert_hashtags_to_brackets(content)

# Write the modified content to a new file
with open("output.md", "w", encoding="utf-8") as file:
    file.write(converted_content)

print("Conversion complete! Check output.md")
