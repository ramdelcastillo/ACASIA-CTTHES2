import os

# Define the base directory
BASE_DIR = r"C:\Users\janva\Downloads"

# Target folders
TARGET_FOLDERS = ["AS1", "AS2", "Manager1", "Manager2", "Director1", "Director2"]

# List of filenames from your sample
FILENAMES = [
    "COPY_EXTERNAL_1.docx",
    "COPY_INTERNAL_1.docx",
    "COPY_NON_EXTERNAL_1.docx",
    "COPY_NON_INTERNAL_1.docx",
    "COPY_NON_OTHERS_1.docx",
    "COPY_OTHERS_1.docx",
    "DELETE_1.docx",
    "DELETE_NON_1.docx",
    "MOVE_EXTERNAL_1.docx",
    "MOVE_INTERNAL_1.docx",
    "MOVE_NON_EXTERNAL_1.docx",
    "MOVE_NON_INTERNAL_1.docx",
    "MOVE_NON_OTHERS_1.docx",
    "MOVE_OTHERS_1.docx",
    "OPEN.docx",
    "OPENWMOD.docx",
    "OPENWMOD_NON.docx",
    "OPEN_NON.docx"
]


def create_files_in_target_folders():
    for folder in TARGET_FOLDERS:
        folder_path = os.path.join(BASE_DIR, folder)
        os.makedirs(folder_path, exist_ok=True)  # Ensure folder exists

        for filename in FILENAMES:
            parts = filename.split("_")
            if parts[-1][0].isdigit():  # If last part starts with a number
                base_name = "_".join(parts[:-1])  # Everything before the number
                extension = parts[-1].split(".")[-1]  # Extract extension

                # Create 1000 copies
                for i in range(1, 1001):
                    new_filename = f"{folder}_{base_name}_{i}.{extension}"
                    file_path = os.path.join(folder_path, new_filename)
                    open(file_path, "w").close()

            else:
                # Create just one copy for files without numbers
                new_filename = f"{folder}_{filename}"
                file_path = os.path.join(folder_path, new_filename)
                open(file_path, "w").close()

        print(f"✅ Files created in: {folder_path}")


# Run the function
create_files_in_target_folders()
