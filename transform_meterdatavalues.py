#!/usr/bin/env python3

import json
import os

from datetime import datetime

DATA_FOLDER = os.getenv("DATA_FOLDER")

folder = DATA_FOLDER
date = datetime.now()

filename = os.path.join(folder, date.strftime("%Y%m%d") + "-electricity-data.json")

# Do something like this : https://github.com/klausj1/homeassistant-statistics/blob/main/assets/min_max_mean.tsv