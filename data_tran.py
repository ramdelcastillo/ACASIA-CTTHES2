import pandas as pd
import os
import json
import logging
from datetime import datetime

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - INFO - %(message)s",
)

def data_transformation():
    input_csv = config["derived_data"]
    output_csv = config["transformed_data"]

    logging.info(f"Starting data transformation. Loading dataset from {input_csv}.")
    df = pd.read_csv(input_csv)

    if df.empty:
        logging.warning(f"{input_csv} is empty. Skipping data transformation.")
        return

    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    logging.info("Standardized column headers.")

    mappings = {
        "computer_user_role": {"Administrative Staff": 1, "Manager": 2, "Director": 3},
        "file_type": {"Confidential": 1, "Non-confidential": 2},
        "fileaccesstype": {
            "File Opening": 1,
            "File Modification": 2,
            "File Deletion": 3,
            "File Move": 4,
            "File Copy": 5
        },
        "computerid": {"Computer A0": 1, "Computer A1": 2, "Computer C0": 3, "Computer C1": 4, "Computer D": 5},
        "computer_user_location": {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4},
        "computerroom":{"Room A": 1, "Room C": 3, "Room D": 4}
    }

    for column, mapping in mappings.items():
        if column in df.columns:
            df[column] = df[column].map(mapping).fillna(0).astype(int)
            logging.info(f"Encoded {column} using predefined mapping.")

    if "actuallocationofusername" in df.columns:
        df.rename(columns={"actuallocationofusername": "computer_user_location"}, inplace=True)
        logging.info("Renamed 'actuallocationofusername' to 'computer_user_location'.")

    if "nearby_user_roles" in df.columns:
        df["nearby_user_roles"] = df["nearby_user_roles"].fillna("")
        role_mapping = {
            "Administrative Staff": "administrative_staff_count",
            "Manager": "manager_count",
            "Director": "director_count"
        }
        for role, column_name in role_mapping.items():
            df[column_name] = df["nearby_user_roles"].apply(lambda x: x.split(", ").count(role.strip()))
            logging.info(f"Processed nearby user roles: {column_name}")

    if {"timestamp", "shift_start", "shift_end", "day_type"}.issubset(df.columns):
        def determine_shift_status(row):
            try:
                timestamp = datetime.fromisoformat(row["timestamp"]) if isinstance(row["timestamp"], str) else datetime.fromtimestamp(float(row["timestamp"]))
                shift_start = datetime.strptime(row["shift_start"], "%H:%M:%S").time()
                shift_end = datetime.strptime(row["shift_end"], "%H:%M:%S").time()
                day_of_week = timestamp.weekday()
                shift_valid = (row["day_type"].lower() == "weekday" and day_of_week < 5) or \
                              (row["day_type"].lower() == "weekend" and day_of_week >= 5)
                return 1 if shift_valid and shift_start <= timestamp.time() <= shift_end else 0
            except Exception as e:
                logging.warning(f"Error processing shift status for row: {row} | Error: {e}")
                return 0

        df["shift_status"] = df.apply(determine_shift_status, axis=1)
        logging.info("Determined shift status for all records.")

    required_columns = [
        "timestamp", "username", "computer_user_role", "nearbyusers", 
        "administrative_staff_count", "manager_count", "director_count",
        "computerid", "computer_user_location", "computerroom",
        "filedestinationdirectory", "file_destination",
        "shift_start", "shift_end", "shift_status",
        "fileaccesstype", "file_type"
    ]

    for col in required_columns:
        if col not in df.columns:
            df[col] = 0  # Fill missing ones with zero 

    df = df[required_columns]
    logging.info("Rearranged dataset columns to match the required order.")

    df.to_csv(output_csv, index=False)
    logging.info(f"Saved transformed data to {output_csv}.")
    logging.info(f"Data transformation completed. {df.shape[0]} rows processed.")

if __name__ == "__main__":
    data_transformation()
