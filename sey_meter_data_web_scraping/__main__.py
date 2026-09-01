from . import collect_meterdatavalues

import json
import os
import sys
import requests
from datetime import datetime, timedelta
from pathlib import Path

OPTIONS_FILE = Path("/data/options.json")

HA_API_URL = os.environ.get("HA_URL", "http://supervisor/core/api")
HA_TOKEN = os.environ.get("HA_TOKEN") or os.environ.get("SUPERVISOR_TOKEN", "")


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


def _fetch_price_sensor(entity_id):
    response = requests.get(
        f"{HA_API_URL}/states/{entity_id}",
        headers={"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"},
        timeout=10,
    )
    response.raise_for_status()
    return float(response.json()["state"])


def load_prices():
    if not HA_TOKEN:
        raise RuntimeError(
            "No Home Assistant API token available: set SUPERVISOR_TOKEN (provided automatically "
            "inside a Home Assistant add-on with homeassistant_api: true) or HA_TOKEN (for local/dev use)."
        )

    # Electricity price sensors report ct/kWh; SeyDataSaver expects CHF/kWh.
    electricity_consumption_high_tariff = _fetch_price_sensor("sensor.electricity_price_consumption_high_tariff") / 100.0
    electricity_consumption_low_tariff = _fetch_price_sensor("sensor.electricity_price_consumption_low_tariff") / 100.0
    electricity_returned_to_grid_tariff = _fetch_price_sensor("sensor.electricity_price_returned_to_grid_tariff") / 100.0
    # Water price sensor already reports CHF/m³.
    water_consumption_tariff = _fetch_price_sensor("sensor.water_price_consumption_tariff")

    return {
        "electricity_consumption_high_tariff": electricity_consumption_high_tariff,
        "electricity_consumption_low_tariff": electricity_consumption_low_tariff,
        "electricity_returned_to_grid_tariff": electricity_returned_to_grid_tariff,
        "water_consumption_tariff": water_consumption_tariff,
    }


if __name__ == '__main__':
    settings = load_settings()
    prices = load_prices()

    print("Tariffs (CHF):")
    print(f"  Electricity consumption, high tariff: {prices['electricity_consumption_high_tariff']:.2f} CHF/kWh")
    print(f"  Electricity consumption, low tariff:  {prices['electricity_consumption_low_tariff']:.2f} CHF/kWh")
    print(f"  Electricity returned to grid:         {prices['electricity_returned_to_grid_tariff']:.2f} CHF/kWh")
    print(f"  Water consumption:                    {prices['water_consumption_tariff']:.2f} CHF/m³")

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
        prices,
    )

