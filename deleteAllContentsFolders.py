import os
import shutil

# List of target folders
directories = [
    r"C:\Users\janva\Downloads\AS1",
    r"C:\Users\janva\Downloads\AS1_InternalFolder",
    r"C:\Users\janva\Downloads\AS2",
    r"C:\Users\janva\Downloads\AS2_InternalFolder",
    r"C:\Users\janva\Downloads\Director1",
    r"C:\Users\janva\Downloads\Director1_InternalFolder",
    r"C:\Users\janva\Downloads\Director2",
    r"C:\Users\janva\Downloads\Director2_InternalFolder",
    r"C:\Users\janva\Downloads\ExternalDrive",
    r"C:\Users\janva\Downloads\Manager1",
    r"C:\Users\janva\Downloads\Manager1_InternalFolder",
    r"C:\Users\janva\Downloads\Manager2",
    r"C:\Users\janva\Downloads\Manager2_InternalFolder",
]

def delete_folder_contents(directory):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist, skipping.")
        return

    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        try:
            if os.path.isfile(item_path):
                os.remove(item_path)  # Delete file
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)  # Delete subfolder and its contents
        except Exception as e:
            print(f"Error deleting {item_path}: {e}")

    print(f"All contents inside {directory} have been deleted, but the folder remains.")

# Delete contents for each directory
for dir_path in directories:
    delete_folder_contents(dir_path)
