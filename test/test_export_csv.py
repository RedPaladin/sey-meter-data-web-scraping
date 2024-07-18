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

        dt = datetime(2024, 6, 20)

        saver = SeyDataSaver(OUTPUT_FOLDER, dt)

        data_electricity = load_data(os.path.join(REFERENCE_FOLDER, "20240620-electricity-data.json"))

        data_water = load_data(os.path.join(REFERENCE_FOLDER, "20240620-water-data.json"))

        saver.save(data_electricity, data_water)

        saver.save_sums()

        self.assertTrue(os.path.exists(os.path.join(OUTPUT_FOLDER, "last_sums.json")))

    def tearDown(self):
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)

if __name__ == '__main__':
    unittest.main()