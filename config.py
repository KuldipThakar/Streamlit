from datetime import date
import os

# Today's date for deadline calculation
TODAY = date.today()

# Directory containing project files
PROJECT_DATA_DIR = "data/"

# Predefined project files

#url = "https://bplmedtech-my.sharepoint.com/:x:/g/personal/kuldip_thakar_bpl_in/EUQLMHc4tqJCnjZN7Yri-yoBaaVuqijjpXgtzHqJ4ighHw?e=77zfrZ"
file_path = "E:\\OneDrive - BPL Medical Technologies Pvt. Ltd\\Exports\\eeee.xlsx"

PROJECT_FILES = {

    "CView FD": file_path,
    "VIVID View ": os.path.join(PROJECT_DATA_DIR, "data.xlsx"),
    "Patient Monitor": os.path.join(PROJECT_DATA_DIR, "1.csv"),
    "ECG": os.path.join(PROJECT_DATA_DIR, "C-ray Pro Plus Cview(II).xlsx"),
    "Project 5": os.path.join(PROJECT_DATA_DIR, "C-ray Pro Plus Cview(II).xlsx"),
    "Project 6": os.path.join(PROJECT_DATA_DIR, "data.xlsx"),
}

