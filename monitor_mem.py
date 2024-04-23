import csv
import os
import time
from datetime import datetime

import psutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HISTORY_FILE_PATH = f"{SCRIPT_DIR}/mem_history.tsv"


def get_current_memory_usage():
    # Thanks https://www.geeksforgeeks.org/how-to-get-current-cpu-and-ram-usage-in-python/
    virtual_mem_usage_info = psutil.virtual_memory()
    memory_percent_used = virtual_mem_usage_info[2]
    memory_used_in_gb = virtual_mem_usage_info[3] / 10 ** 9
    return round(memory_used_in_gb, 1), memory_percent_used


def record_data(timestamp, memory_used, percent_used):
    with open(HISTORY_FILE_PATH, "a") as mem_file:
        writer = csv.writer(mem_file, delimiter="\t")
        writer.writerow([timestamp, memory_used, percent_used])


def main():
    # Initiate the file to save data to
    if not os.path.exists(HISTORY_FILE_PATH):
        with open(HISTORY_FILE_PATH, "w+") as mem_file:
            writer = csv.writer(mem_file, delimiter="\t")
            writer.writerow(["timestamp", "memory_used_gb", "percent_mem_used"])

    # Record mem usage level every 5 seconds
    while True:
        time.sleep(5)
        utc_timestamp = datetime.utcnow()
        memory_used, percent_used = get_current_memory_usage()
        record_data(utc_timestamp, memory_used, percent_used)


if __name__ == "__main__":
    main()
