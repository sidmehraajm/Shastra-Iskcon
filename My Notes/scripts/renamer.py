import os

def rename_files(folder_path, search_text="", replace_text="", prefix="", suffix=""):
    """
    Add text to filenames or search/replace in a folder and its subfolders.
    
    Parameters:
    folder_path: Path to the root folder
    search_text: Text to find in filenames (optional)
    replace_text: Text to replace with (optional)
    prefix: Text to add at start of filename (optional)
    suffix: Text to add at end of filename (before extension) (optional)
    """
    print(f"Starting rename process in: {folder_path}")
    
    # Counter for processed folders and files
    folder_count = 0
    file_count = 0
    
    # Walk through folder and subfolders
    for root, dirs, files in os.walk(folder_path):
        folder_count += 1
        print(f"Processing folder: {root}")
        print(f"Found {len(files)} files in this folder")
        
        for filename in files:
            file_count += 1
            # Get file path and extension
            file_path = os.path.join(root, filename)
            name, ext = os.path.splitext(filename)
            
            # Initialize new name
            new_name = name
            
            # Apply search and replace if specified
            if search_text and replace_text:
                new_name = new_name.replace(search_text, replace_text)
            
            # Add prefix and/or suffix if specified
            new_name = f"{prefix}{new_name}{suffix}"
            
            # Create new filename with extension
            new_filename = f"{new_name}{ext}"
            new_file_path = os.path.join(root, new_filename)
            
            # Skip if no change to filename
            if new_filename == filename:
                print(f"No changes needed for: {filename}")
                continue
                
            # Rename the file
            try:
                os.rename(file_path, new_file_path)
                print(f"Renamed: {filename} -> {new_filename}")
            except Exception as e:
                print(f"Error renaming {filename} in {root}: {e}")
    
    print(f"Finished! Processed {folder_count} folders and {file_count} files.")

def main():
    # Get folder path from user
    folder_path = input("Enter the folder path: ").strip()
    
    # Verify folder exists and is accessible
    if not os.path.isdir(folder_path):
        print("Invalid or inaccessible folder path!")
        return
    
    # Get absolute path for clarity
    folder_path = os.path.abspath(folder_path)
    print(f"Working with absolute path: {folder_path}")
    
    # Get renaming options
    mode = input("Choose mode (1: Add prefix/suffix, 2: Search and replace, 3: Both): ").strip()
    
    prefix = ""
    suffix = ""
    search_text = ""
    replace_text = ""
    
    if mode in ["1", "3"]:
        prefix = input("Enter prefix to add (or press Enter for none): ").strip()
        suffix = input("Enter suffix to add (or press Enter for none): ").strip()
    
    if mode in ["2", "3"]:
        search_text = input("Enter text to search for: ").strip()
        replace_text = input("Enter replacement text: ").strip()
    
    # Execute renaming
    rename_files(folder_path, search_text, replace_text, prefix, suffix)
    print("Renaming process complete!")

if __name__ == "__main__":
    main()