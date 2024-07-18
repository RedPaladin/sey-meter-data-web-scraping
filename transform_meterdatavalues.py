#!/usr/bin/env python3

import json
import os

from datetime import datetime, timedelta

DATA_FOLDER = os.getenv("DATA_FOLDER")

folder = DATA_FOLDER
date = datetime.now()

#filename = os.path.join(folder, date.strftime("%Y%m%d") + "-electricity-data.json")
filename = os.path.join("data", "20240620-electricity-data.json")

data = None

with open(filename, "r", encoding="utf-8") as f:
    data = json.loads(f.read())

assert len(data) == 2

for d in data[0]['data']:
    dt = d['x']
    cons = d['y']

    dt = datetime.fromisoformat(dt) - timedelta(hours=1)
    dt = dt.strftime("%d.%m.%Y %H:%M")
    print(f"sensor.power_consumption\tkWh\t{dt}\t{cons:.3f}\t{cons:.3f}\t{cons:.3f}")

# Do something like this : https://github.com/klausj1/homeassistant-statistics/blob/main/assets/min_max_mean.tsv