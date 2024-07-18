#!/usr/bin/env python3

import json
import os

from datetime import datetime, timedelta

DATA_FOLDER = os.getenv("DATA_FOLDER")

folder = DATA_FOLDER
date = datetime.now()

#filename = os.path.join(folder, date.strftime("%Y%m%d") + "-electricity-data.json")

def load_data(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return json.loads(f.read())

class SeyDataSaver:
    def __init__(self, folder, dt) -> None:
        self._sums = {}
        self._folder = folder
        self._date = dt.strftime("%Y%m%d")
        self._last_sums_filename = os.path.join(self._folder, "last_sums.json")
        self._load_sums()

    def _extract_data(self, data, entity_id, unit):
        # print the headers
        yield "statistic_id\tunit\tstart\tsum"

        sum = self._sums.get(entity_id, 0.0)

        for d in data:
            dt = d['x']
            state = d['y']

            dt = datetime.fromisoformat(dt) - timedelta(hours=1)
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

    def save(self, filename, data, entity_id, unit):
        full_filename = os.path.join(self._folder, f"{self._date}-{filename}")

        self._save_data(full_filename, self._extract_data(data, entity_id, unit))
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

saver = SeyDataSaver("data", dt)

saver.save("power-production-data.tsv", data[0]['data'], "sensor:sey_power_production", "kWh")
saver.save("power-consumption-data.tsv", data[1]['data'], "sensor:sey_power_consumption", "kWh")

data = load_data(os.path.join("data", "20240620-water-data.json"))

assert len(data) == 1

saver.save("water-consumption-data.tsv", data[0]['data'], "sensor:sey_water_consumption", "m³")

saver.save_sums()

# Do something like this : https://github.com/klausj1/homeassistant-statistics/blob/main/assets/min_max_mean.tsv