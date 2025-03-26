import os
import logging
import json
import time
from data_imp import create_or_append_csv, data_imputation
from data_der import data_derivation
from data_tran import data_transformation

with open("config.json", "r") as file:
    config = json.load(file)

logging.basicConfig(
    filename=config["log_file"],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def run_pipeline():
    try:
        logging.info("=== Step 1: Running Data Imputation ===")
        new_data_added = create_or_append_csv()  # Must return True if new logs were appended

        if not new_data_added:
            logging.info("No new logs detected. Skipping remaining steps.")
            return  # Exit if no new logs

        data_imputation()
        logging.info("Data Imputation Completed Successfully.")

        logging.info("=== Step 2: Running Data Derivation ===")
        data_derivation()
        logging.info("Data Derivation Completed Successfully.")

        logging.info("=== Step 3: Running Data Transformation ===")
        data_transformation()
        logging.info("Data Transformation Completed Successfully.")

        logging.info("=== Pipeline Execution Completed ===")

    except Exception as e:
        logging.error(f"Pipeline execution failed: {e}")
        print(f"Error encountered! Check preprocessing.log for details.")

if __name__ == "__main__":
    watched_file = config["json_file"]  
    last_modified = None

    print(f"Watching for changes in '{watched_file}'...\nPress Ctrl+C to stop.\n")

    while True:
        try:
            if os.path.exists(watched_file):
                current_modified = os.path.getmtime(watched_file)

                if last_modified is None:
                    last_modified = current_modified 
                elif current_modified != last_modified:
                    print("Detected update in save_updated.json. Running preprocessing pipeline...\n")
                    run_pipeline()
                    last_modified = current_modified
                    print("Data preprocessing completed\n") 

            time.sleep(2)  

        except KeyboardInterrupt:
            print("File watcher stopped by user.")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)
