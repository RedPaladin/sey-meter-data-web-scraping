from . import collect_meterdatavalues

import os

import sys
from datetime import datetime, timedelta

USERNAME = os.getenv("SEY_USERNAME")
PASSWORD = os.getenv("SEY_PASSWORD")
SUBJECT_ID = os.getenv("SEY_SUBJECT_ID")

ELECTRICAL_CONTRACT_ID = os.getenv("SEY_ELECTRICAL_CONTRACT_ID")
WATER_CONTRACT_ID = os.getenv("SEY_WATER_CONTRACT_ID")

DATA_FOLDER = os.getenv("DATA_FOLDER")

if __name__ == '__main__':

    if len(sys.argv) > 1:
        dt = datetime.strptime(sys.argv[1], "%Y%m%d")
    else:
        dt = datetime.now() - timedelta(days = 2)

    collect_meterdatavalues(USERNAME, PASSWORD, ELECTRICAL_CONTRACT_ID, WATER_CONTRACT_ID, SUBJECT_ID, DATA_FOLDER, dt)

