import pandas as pd
import re
import os
import json
import logging

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - INFO - %(message)s",
)

def data_derivation():
    input_csv = config["imputed_data"]
    config_db = config["config_db"]
    output_csv = config["derived_data"]

    logging.info(f"Loading dataset from {input_csv} and configuration from {config_db}.")

    df = pd.read_csv(input_csv)
    config_data = pd.read_csv(config_db)

    if df.empty:
        logging.warning(f"{input_csv} is empty. Skipping data derivation.")
        return

    config_data.columns = config_data.columns.str.strip().str.lower().str.replace(" ", "_")
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    df["username"] = df["username"].str.strip().str.lower()
    config_data["user_name"] = config_data["user_name"].str.strip().str.lower()

    logging.info("Standardized column headers and usernames.")

    column_mappings = {
        "user_name": "username",
        "user_role": "computer_user_role",
        "assigned_computer_id": "assigned_computer_id",
        "shift_start": "shift_start",
        "shift_end": "shift_end",
        "daytype": "day_type",
        "computer_id": "computerid",
    }
    config_data.rename(columns=column_mappings, inplace=True)

    if "computer_user_role" not in config_data.columns or "username" not in df.columns:
        logging.error("Missing required columns in configuration or dataset.")
        raise KeyError("Missing 'computer_user_role' in config_db or 'username' in input_csv")

    user_role_mapping = config_data.set_index("username")["computer_user_role"].to_dict()
    df["computer_user_role"] = df["username"].map(user_role_mapping).fillna("Unknown")
    logging.info("Mapped usernames to computer user roles.")

    role_mapping = config_data.set_index("computer_user_role")[["shift_start", "shift_end", "day_type", "assigned_computer_id"]].to_dict()
    df["shift_start"] = df["computer_user_role"].map(role_mapping["shift_start"]).fillna("Unknown")
    df["shift_end"] = df["computer_user_role"].map(role_mapping["shift_end"]).fillna("Unknown")
    df["day_type"] = df["computer_user_role"].map(role_mapping["day_type"]).fillna("Unknown")
    df["assigned_computer_id"] = df["computer_user_role"].map(role_mapping["assigned_computer_id"]).fillna("Unknown")
    logging.info("Mapped computer user roles to shift and computer assignments.")

    def get_nearby_user_roles(nearby_users):
        if pd.isnull(nearby_users) or nearby_users.strip() == "":
            return "Unknown"
        try:
            nearby_users_list = eval(nearby_users) if isinstance(nearby_users, str) else nearby_users
            roles = [user_role_mapping.get(user.strip().lower(), "Unknown") for user in nearby_users_list]
            return ", ".join(roles) if roles else "Unknown"
        except Exception as e:
            logging.warning(f"Error processing nearby users: {nearby_users} | Error: {e}")
            return "Unknown"

    df["nearby_user_roles"] = df["nearbyusers"].apply(get_nearby_user_roles)
    logging.info("Derived nearby user roles.")

    def extract_top_folder(path):
        if pd.isnull(path) or not isinstance(path, str) or path.strip() == "":
            return "Unknown"
        path_parts = re.split(r"[\\/]", path)
        if len(path_parts) < 2:
            return "Unknown"
        if path.startswith("C:\\Users") and len(path_parts) > 2:
            return path_parts[2]
        if re.match(r"^[A-Z]:\\", path):
            return path_parts[1]
        return "Unknown"

    def determine_file_destination(dest_dir):
        if pd.isnull(dest_dir) or not isinstance(dest_dir, str):
            return "Unknown"
        if dest_dir.strip().lower() == "recycle bin":
            return "Recycle Bin"
        return extract_top_folder(dest_dir)

    df["file_destination"] = df["filedestinationdirectory"].apply(determine_file_destination)
    logging.info("Extracted file destination directory.")

    def get_file_type(file_name):
        if pd.isnull(file_name) or not isinstance(file_name, str):
            return "Unknown"
        file_name = file_name.strip()
        base_name, ext = os.path.splitext(file_name)
        return "Non-confidential" if "NON" in base_name else "Confidential"

    df["file_destination_name"] = df["filedestinationdirectory"].apply(lambda x: x.split("\\")[-1] if pd.notnull(x) else "Unknown")

    df["file_type"] = df["file_destination_name"].apply(get_file_type)
    logging.info("Classified files as Confidential or Non-confidential.")

    df.to_csv(output_csv, index=False)
    logging.info(f"Data derivation completed. Saved to {output_csv}. {df.shape[0]} rows processed.")

if __name__ == "__main__":
    data_derivation()
