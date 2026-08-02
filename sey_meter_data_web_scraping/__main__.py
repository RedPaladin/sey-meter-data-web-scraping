from . import collect_meterdatavalues

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

OPTIONS_FILE = Path("/data/options.json")


def load_settings():
    settings = {}
    if OPTIONS_FILE.exists():
        with OPTIONS_FILE.open("r", encoding="utf-8") as handle:
            settings = json.load(handle)

    return {
        "SEY_USERNAME": settings.get("sey_username", ""),
        "SEY_PASSWORD": settings.get("sey_password", ""),
        "SEY_SUBJECT_ID": settings.get("sey_subject_id", ""),
        "SEY_ELECTRICAL_CONTRACT_ID": settings.get("sey_electrical_contract_id", ""),
        "SEY_WATER_CONTRACT_ID": settings.get("sey_water_contract_id", ""),
        "DATA_FOLDER": settings.get("data_folder", "/config/sey_meter_data_web_scraping"),
    }


if __name__ == '__main__':
    settings = load_settings()

    if len(sys.argv) > 1:
        dt = datetime.strptime(sys.argv[1], "%Y%m%d")
    else:
        dt = datetime.now() - timedelta(days = 2)

    collect_meterdatavalues(
        settings["SEY_USERNAME"],
        settings["SEY_PASSWORD"],
        settings["SEY_ELECTRICAL_CONTRACT_ID"],
        settings["SEY_WATER_CONTRACT_ID"],
        settings["SEY_SUBJECT_ID"],
        settings["DATA_FOLDER"],
        dt,
    )

