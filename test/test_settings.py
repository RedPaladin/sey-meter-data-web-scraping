import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from sey_meter_data_web_scraping import __main__ as main


class SettingsLoadingTestCase(unittest.TestCase):
    def test_load_settings_uses_home_assistant_options_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            options_path = Path(tmpdir) / "options.json"
            options = {
                "sey_username": "uiuser",
                "sey_password": "uipass",
                "sey_subject_id": "subject",
                "sey_electrical_contract_id": "el-contract",
                "sey_water_contract_id": "water-contract",
                "data_folder": "/config/sey",
            }
            options_path.write_text(json.dumps(options), encoding="utf-8")

            with patch.object(main, "OPTIONS_FILE", options_path):
                settings = main.load_settings()

            self.assertEqual(settings["SEY_USERNAME"], "uiuser")
            self.assertEqual(settings["SEY_PASSWORD"], "uipass")
            self.assertEqual(settings["SEY_SUBJECT_ID"], "subject")
            self.assertEqual(settings["SEY_ELECTRICAL_CONTRACT_ID"], "el-contract")
            self.assertEqual(settings["SEY_WATER_CONTRACT_ID"], "water-contract")
            self.assertEqual(settings["DATA_FOLDER"], "/config/sey")


class PricesLoadingTestCase(unittest.TestCase):
    def test_load_prices_fetches_from_home_assistant_api(self):
        def fake_get(url, headers=None, timeout=None):
            entity_id = url.rsplit("/", 1)[-1]
            # Electricity sensors report ct/kWh; water reports CHF/m³ directly.
            state_by_entity = {
                "sensor.electricity_price_consumption_high_tariff": "30.00",
                "sensor.electricity_price_consumption_low_tariff": "20.00",
                "sensor.electricity_price_returned_to_grid_tariff": "10.00",
                "sensor.water_price_consumption_tariff": "3.50",
            }
            response = MagicMock()
            response.json.return_value = {"state": state_by_entity[entity_id]}
            response.raise_for_status.return_value = None
            return response

        with patch.object(main.requests, "get", side_effect=fake_get):
            prices = main.load_prices()

        self.assertEqual(prices["electricity_consumption_high_tariff"], 0.30)
        self.assertEqual(prices["electricity_consumption_low_tariff"], 0.20)
        self.assertEqual(prices["electricity_returned_to_grid_tariff"], 0.10)
        self.assertEqual(prices["water_consumption_tariff"], 3.50)

    def test_load_prices_raises_when_no_token_available(self):
        with patch.object(main, "HA_TOKEN", ""):
            with self.assertRaises(RuntimeError):
                main.load_prices()


if __name__ == "__main__":
    unittest.main()
