import json
import pandas as pd
import os
import logging

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - INFO - %(message)s",
)

def create_or_append_csv():
    json_file = config["json_file"]
    raw_csv = config["raw_data"]
    tracker_file = config["tracker_file"]

    try:
        with open(json_file, 'r') as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON file: {e}")
        raise ValueError("Invalid JSON format")

    if not isinstance(data, list):
        logging.warning(f"Unexpected format in {json_file}. Expected a list of logs.")
        return False

    total_logs = len(data)

    # Track progress
    last_processed = 0
    if os.path.exists(tracker_file):
        with open(tracker_file, "r") as f:
            try:
                last_processed = int(f.read().strip())
            except ValueError:
                last_processed = 0

    new_logs = data[last_processed:]
    if not new_logs:
        logging.info("No new logs to process.")
        return False

    df = pd.DataFrame(new_logs)

    if os.path.exists(raw_csv):
        df.to_csv(raw_csv, mode='a', header=False, index=False)
        logging.info(f"Appended {df.shape[0]} new rows to {raw_csv}.")
    else:
        df.to_csv(raw_csv, index=False)
        logging.info(f"Created {raw_csv} with {df.shape[0]} rows.")

    with open(tracker_file, "w") as f:
        f.write(str(total_logs))
    logging.info(f"Updated log tracker to {total_logs} entries.")

    return True

def data_imputation():
    raw_csv = config["raw_data"]
    imputed_csv = config["imputed_data"]
    backup_csv = config["backup_data"]

    if not os.path.exists(raw_csv) or os.stat(raw_csv).st_size == 0:
        logging.warning(f"No data in {raw_csv}. Skipping imputation.")
        return

    df = pd.read_csv(raw_csv)
    logging.info(f"Loaded raw data from {raw_csv}. {df.shape[0]} rows, {df.shape[1]} columns.")

    # Backup
    if os.path.exists(backup_csv):
        df.to_csv(backup_csv, mode="a", header=False, index=False)
        logging.info(f"Appended raw data to backup: {backup_csv}. {df.shape[0]} rows added.")
    else:
        df.to_csv(backup_csv, index=False)
        logging.info(f"Created backup file: {backup_csv}. {df.shape[0]} rows saved.")

    if "ActualLocationOfUsername" in df.columns:
        df.rename(columns={"ActualLocationOfUsername": "computer_user_location"}, inplace=True)
        logging.info("Renamed 'ActualLocationOfUsername' to 'computer_user_location'.")

    for column in df.columns:
        if df[column].isnull().any():
            before_missing = df[column].isnull().sum()

            if column == "Timestamp":
                df[column] = df[column].fillna(method="ffill").fillna(method="bfill")
            elif column in ["ComputerID"]:
                df[column].fillna(df[column].median(), inplace=True)
            elif column in ["Username", "computer_user_location", "ComputerRoom", "fileAccessType"]:
                df[column].fillna(df[column].mode()[0] if not df[column].mode().empty else "Unknown", inplace=True)
            elif column == "fileDestinationDirectory":
                df[column].fillna("Unknown Directory", inplace=True)
            elif column == "NearbyUsers":
                df[column] = df[column].apply(lambda x: x if isinstance(x, str) else "Unknown")

            after_missing = df[column].isnull().sum()
            logging.info(f"Filled {before_missing - after_missing} missing values in '{column}'.")

    # Convert Unix Timestamp to readable datetime
    if "Timestamp" in df.columns:
        df["Timestamp"] = pd.to_datetime(df["Timestamp"], unit="s").dt.strftime("%Y-%m-%d %H:%M:%S")
        logging.info("Converted Unix timestamp to standard datetime format.")

    df.to_csv(imputed_csv, index=False)
    logging.info(f"Saved imputed data to {imputed_csv}. {df.shape[0]} rows processed.")

if __name__ == "__main__":
    create_or_append_csv()
    data_imputation()
