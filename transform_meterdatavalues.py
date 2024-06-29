#!/usr/bin/env python3

import json
import os
from enum import Enum

from datetime import datetime, timedelta

DATA_FOLDER = os.getenv("DATA_FOLDER")

folder = DATA_FOLDER
date = datetime.now()

#filename = os.path.join(folder, date.strftime("%Y%m%d") + "-electricity-data.json")

def load_data(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.loads(f.read())
    
class Mode(Enum):
    DATA_NO_BI_TARIFICATION_MODE = 0
    COST_NO_BI_TARIFICATION_MODE = 1
    DATA_BI_TARIFICATION_HIGH_TARIFF_MODE = 2
    DATA_BI_TARIFICATION_LOW_TARIFF_MODE = 3
    COST_BI_TARIFICATION_HIGH_TARIFF_MODE = 4
    COST_BI_TARIFICATION_LOW_TARIFF_MODE = 5

class SeyDataSaver:
    def __init__(self, folder, dt) -> None:
        self._sums = {}
        self._folder = folder
        self._date = dt.strftime("%Y%m%d")
        self._last_sums_filename = os.path.join(self._folder, "last_sums.json")
        self._load_sums()

    def _is_high_tariff_datetime(self, dt : datetime) -> bool:
        if dt.weekday() in range(0, 5):
            return dt.hour >= 6 and dt.hour < 22
        else: # weekend
            return (dt.hour >= 10 and dt.hour < 13) or (dt.hour >= 17 and dt.hour < 22)

    def _extract_data(self, data, entity_id, unit, mode : Mode, tariff: float = None):
        # print the headers
        yield "statistic_id\tunit\tstart\tsum"

        sum = self._sums.get(entity_id, 0.0)

        for d in data:
            dt = d['x']
            state = d['y']

            dt = datetime.fromisoformat(dt) - timedelta(hours=1)

            match mode:
                case Mode.DATA_NO_BI_TARIFICATION_MODE:
                    pass
                case Mode.COST_NO_BI_TARIFICATION_MODE:
                    assert tariff is not None, "Not tariff provided to calculate the cost"
                    state *= tariff
                case Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE:
                    if not self._is_high_tariff_datetime(dt):
                        continue
                case Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE:
                    if self._is_high_tariff_datetime(dt):
                        assert tariff is not None, "Not tariff provided to calculate the cost"
                        state *= tariff
                    else:
                        continue
                case Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE:
                    if self._is_high_tariff_datetime(dt):
                        continue
                case Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE:
                    if not self._is_high_tariff_datetime(dt):
                        assert tariff is not None, "Not tariff provided to calculate the cost"
                        state *= tariff
                    else:
                        continue
                case _:
                    assert(False)

            dt = dt.strftime("%d.%m.%Y %H:%M")

            yield f"{entity_id}\t{unit}\t{dt}\t{(state + sum):.3f}"

            sum += state

        self._last_sum = sum

    def _save_data(self, filename, generator):
        with open(filename, "w", encoding="utf-8") as f:
            print(f"Saving file: {filename}")
            for line in generator:
                #print(line)
                f.write(line + "\n")

    def save(self, filename, data, entity_id, unit, mode : Mode, tariff: float = None):
        full_filename = os.path.join(self._folder, f"{self._date}-{filename}")

        self._save_data(full_filename, self._extract_data(data, entity_id, unit, mode, tariff))
        self._sums[entity_id] = self._last_sum

    def _load_sums(self):
        if not os.path.exists(self._last_sums_filename):
            print(f"File does not exist: {self._last_sums_filename}. Let's assume this is the first execution")
            return
        
        with open(self._last_sums_filename, "r", encoding="utf-8") as f:
            print(f"Loading file: {self._last_sums_filename}")
            self._sums = json.loads(f.read())
            if self._date == self._sums['date']:
                print("ERROR: The stored sum from previous run contains already the current date. Script may have been executed twice !")
                quit(1)

    def save_sums(self):
        with open(self._last_sums_filename, "w", encoding="utf-8") as f:
            print(f"Saving file: {self._last_sums_filename}")
            self._sums['date'] = self._date
            f.write(json.dumps(self._sums))

data = load_data(os.path.join("data", "20240620-electricity-data.json"))

assert len(data) == 2

dt = datetime(2024, 6, 20)

if os.path.exists("data/last_sums.json"):
    os.remove("data/last_sums.json")

saver = SeyDataSaver("data", dt)

saver.save("energy-production-data-high-tariff.tsv", data[0]['data'], "sensor:sey_energy_production_high_tariff", "kWh", Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE)
saver.save("energy-production-data-low-tariff.tsv", data[0]['data'], "sensor:sey_energy_production_low_tariff", "kWh", Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE)
tariff = (18.10) * 1.081
saver.save("energy-production-cost-high-tariff.tsv", data[0]['data'], "sensor:sey_energy_production_cost_high_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE, tariff / 100.0)
tariff = (18.10) * 1.081
saver.save("energy-production-cost-low-tariff.tsv", data[0]['data'], "sensor:sey_energy_production_cost_low_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE, tariff / 100.0)

saver.save("energy-consumption-data-high-tariff.tsv", data[1]['data'], "sensor:sey_energy_consumption_high_tariff", "kWh", Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE)
saver.save("energy-consumption-data-low-tariff.tsv", data[1]['data'], "sensor:sey_energy_consumption_low_tariff", "kWh", Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE)
tariff = (21.0 + 13.11 + 0.75 + 2.3 + 0.6 + 0.02 + 0.7 + 0.7 + 0.6 + 1.2) * 1.081
saver.save("energy-consumption-cost-high-tariff.tsv", data[1]['data'], "sensor:sey_energy_consumption_cost_high_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE, tariff / 100.0)
tariff = (18.75 + 7.56 + 0.75 + 2.3 + 0.6 + 0.02 + 0.7 + 0.7 + 0.6 + 1.2) * 1.081
saver.save("energy-consumption-cost-low-tariff.tsv", data[1]['data'], "sensor:sey_energy_consumption_cost_low_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE, tariff / 100.0)

data = load_data(os.path.join("data", "20240620-water-data.json"))

assert len(data) == 1

saver.save("water-consumption-data.tsv", data[0]['data'], "sensor:sey_water_consumption", "m³", Mode.DATA_NO_BI_TARIFICATION_MODE)
tariff = (2.95 + 2.30) * 1.081
saver.save("water-consumption-cost.tsv", data[0]['data'], "sensor:sey_water_consumption_cost", "CHF/m³", Mode.COST_NO_BI_TARIFICATION_MODE, tariff)

saver.save_sums()

# Do something like this : https://github.com/klausj1/homeassistant-statistics/blob/main/assets/min_max_mean.tsv