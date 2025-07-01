import unittest
import os
import shutil
import json
from datetime import datetime, timedelta

from sey_meter_data_web_scraping.utils import SeyWebScraper
from . import OUTPUT_FOLDER

class ImportDataTestCase(unittest.TestCase):

    def setUp(self) -> None:
        self._username = os.getenv("SEY_USERNAME")
        self._password = os.getenv("SEY_PASSWORD")
        self._subject_id = os.getenv("SEY_SUBJECT_ID")
        self._electrical_contract_id = os.getenv("SEY_ELECTRICAL_CONTRACT_ID")
        self._water_contract_id = os.getenv("SEY_WATER_CONTRACT_ID")

        self.assertIsNotNone(self._username, "Environment variable SEY_USERNAME is not set")
        self.assertIsNotNone(self._password, "Environment variable SEY_PASSWORD is not set")
        self.assertIsNotNone(self._subject_id, "Environment variable SEY_SUBJECT_ID is not set")
        self.assertIsNotNone(self._electrical_contract_id, "Environment variable SEY_ELECTRICAL_CONTRACT_ID is not set")
        self.assertIsNotNone(self._water_contract_id, "Environment variable SEY_WATER_CONTRACT_ID is not set")

        if not os.path.exists(OUTPUT_FOLDER):
            os.mkdir(OUTPUT_FOLDER)

    def test_import_data(self):
        
        scrapper = SeyWebScraper(OUTPUT_FOLDER)

        def save_data(filename, data : str):
            print(f"Saving file: {filename}")
            with open(filename, "w", encoding="utf-8") as f:
                f.write(data)

        try:
            scrapper.login(self._username, self._password)

            dt = datetime.now() - timedelta(days = 3)
            
            data_electricity, data_water = scrapper.collect(self._electrical_contract_id, self._water_contract_id, self._subject_id, dt)

            save_data(os.path.join(OUTPUT_FOLDER, "data_electricity.json"), json.dumps(data_electricity, indent=3))
            save_data(os.path.join(OUTPUT_FOLDER, "data_water.json"), json.dumps(data_water, indent=3))

            self.assertIsNotNone(data_electricity)
            self.assertIsNotNone(data_water)
            
            scrapper.logout()
        finally:
            scrapper.close()

    def tearDown(self):
        if os.path.exists(OUTPUT_FOLDER):
            shutil.rmtree(OUTPUT_FOLDER)