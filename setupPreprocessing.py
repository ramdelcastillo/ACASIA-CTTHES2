import os

# Directory path
dir_path = r"C:\Users\janva\PycharmProjects\PythonProject\.venv\Scripts"

# List of specific files to delete
files_to_delete = [
    "transformed_data.csv",
    "derived_data.csv",
    "imputed_data.csv",
    "raw_data_unprocessed.csv",
    "raw_data.csv",
    "preprocessing.log",
    "last_processed_log.txt"
]

# Loop through and delete only the specified files
for file in files_to_delete:
    file_path = os.path.join(dir_path, file)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")
    else:
        print(f"File not found: {file_path}")
