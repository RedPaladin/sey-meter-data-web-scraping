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

def extract_data(data, entity_id, unit):

    # print the headers
    yield "statistic_id\tunit\tstart\tmin\tmax\tmean"

    for d in data:
        dt = d['x']
        cons = d['y']

        dt = datetime.fromisoformat(dt) - timedelta(hours=1)
        dt = dt.strftime("%d.%m.%Y %H:%M")

        yield f"{entity_id}\t{unit}\t{dt}\t{cons:.3f}\t{cons:.3f}\t{cons:.3f}"

def save_data(filename, generator):
    with open(filename, "w", encoding="utf-8") as f:
        for line in generator:
            print(line)
            f.write(line + "\n")

data = load_data(os.path.join("data", "20240620-electricity-data.json"))

assert len(data) == 2

save_data(os.path.join("data", "20240620-power-production-data.tsv"), extract_data(data[0]['data'], "sensor:sey_power_production", "kWh"))
save_data(os.path.join("data", "20240620-power-consumption-data.tsv"), extract_data(data[1]['data'], "sensor:sey_power_consumption", "kWh"))

data = load_data(os.path.join("data", "20240620-water-data.json"))

assert len(data) == 1

save_data(os.path.join("data", "20240620-water-consumption-data.tsv"), extract_data(data[0]['data'], "sensor:sey_water_consumption", "m³"))

# Do something like this : https://github.com/klausj1/homeassistant-statistics/blob/main/assets/min_max_mean.tsv