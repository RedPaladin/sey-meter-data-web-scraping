import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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


if __name__ == "__main__":
    unittest.main()
