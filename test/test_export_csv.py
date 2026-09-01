''' Test export '''

import json
import os
import unittest
import shutil

from datetime import datetime

from sey_meter_data_web_scraping.utils import SeyDataSaver
from . import OUTPUT_FOLDER, REFERENCE_FOLDER

class ExportCsvTestCase(unittest.TestCase):

    def setUp(self) -> None:
        if not os.path.exists(OUTPUT_FOLDER):
            os.mkdir(OUTPUT_FOLDER)

    def test_export_csv(self):

        def load_data(filename):
            print(f"Opening file: {filename}")
            with open(filename, "r", encoding="utf-8") as f:
                return json.loads(f.read())

        dt = datetime(2026, 9, 1)

        saver = SeyDataSaver(OUTPUT_FOLDER, dt)

        data_electricity = load_data(os.path.join(REFERENCE_FOLDER, "electrical_data_20260829.json"))

        data_water = load_data(os.path.join(REFERENCE_FOLDER, "water_json_data_20260829.json"))

        prices = {
            "electricity_consumption_high_tariff": (16.76 + 15.31 + 0.59 + 0.25 + 2.49 + 0.6 + 0.022 + 0.76 + 0.7 + 0.6) * 1.081 / 100.0,
            "electricity_consumption_low_tariff": (14.32 + 9.31 + 0.59 + 0.25 + 2.49 + 0.6 + 0.022 + 0.76 + 0.7 + 0.6) * 1.081 / 100.0,
            "electricity_returned_to_grid_tariff": (12.20 + 1.50) / 100.0,
            "water_consumption_tariff": (2.95 + 2.30) * 1.081,
        }

        saver.save(data_electricity, data_water, prices)

    def tearDown(self):
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)

if __name__ == '__main__':
    unittest.main()