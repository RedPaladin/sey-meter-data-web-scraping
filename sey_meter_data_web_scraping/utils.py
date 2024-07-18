import json
import os
from datetime import datetime, timedelta
from enum import Enum

import requests

from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

class SeyWebScraper:
    ''' Class to Web Scrap from SEY '''

    def __init__(self, output_folder):

        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        self._driver = webdriver.Chrome(options=chrome_options)
        self._driver.implicitly_wait(20)
        self._output_folder = output_folder

        assert os.path.exists(self._output_folder)

    def _screenshot_element(self, elem, filename):
        with open(os.path.join(self._output_folder, filename), "wb") as f:
            f.write(elem.screenshot_as_png)

    def _findkeys(self, node, kv):
        if isinstance(node, list):
            for i in node:
                for x in self._findkeys(i, kv):
                    yield x
        elif isinstance(node, dict):
            if kv in node:
                yield node[kv]
            for j in node.values():
                for x in self._findkeys(j, kv):
                    yield x

    def _get_authorization_token_id(self, logs):

        for entry in logs:
            log = json.loads(entry["message"])["message"]
            l = list(self._findkeys(log, "Authorization"))
            if len(l) > 0:
                return { "Authorization" : str(l[0]) }

    def login(self, username, password):
        ''' Login into SEY '''

        self._driver.get("https://my.yverdon-energies.ch/ebp/login")

        login = self._driver.find_element(By.PARTIAL_LINK_TEXT, 'Vers le login')
        self._screenshot_element(login, "login.png")

        ActionChains(self._driver).move_to_element(login).click().perform()

        username_element = self._driver.find_element(By.ID, "username")

        username_element.send_keys(username)

        self._screenshot_element(username_element, "username.png")

        password_element = self._driver.find_element(By.ID, "password")

        password_element.send_keys(password)

        self._screenshot_element(password_element, "password.png")

        self._driver.save_screenshot(os.path.join(self._output_folder, "screenshot0.png"))

        sign_in = self._driver.find_element(By.ID, "kc-login")

        ActionChains(self._driver).move_to_element(sign_in).click().perform()

        #print(self._driver.get_cookies())

        self._driver.save_screenshot(os.path.join(self._output_folder, "screenshot1.png"))

    def collect(self, electrical_contract_id, water_contract_id, date):
        ''' Collect the data from the SEY '''

        # Wait until this element is visible so we are sure that data are available
        self._driver.find_element(By.XPATH, "//span[contains(text(),'HJ')]")

        # Get the authorization from the Chrome log (this is all the magic comes from!)
        logs = self._driver.get_log("performance")

        header = self._get_authorization_token_id(logs)

        start_dt = datetime.combine(date, datetime.min.time())
        end_dt = datetime.combine(date + timedelta(days = 1), datetime.min.time()) - timedelta(minutes = 1)

        meterdatavalues = requests.get(f"https://backend.yverdon-energies.ch/ebp/meterdatavalues?meteringpoint={electrical_contract_id}&dateFrom={start_dt.isoformat()}&dateTo={end_dt.isoformat()}&intervall=1", headers=header, timeout=10)

        # data in kWh, 1 sample / 1 hour
        electrical_json_data = json.loads(meterdatavalues.content.decode("utf-8"))

        # seems to work only with data from yesterday, not older. Why ?
        meterdatavalues = requests.get(f"https://backend.yverdon-energies.ch/ebp/meterdatavalues?meteringpoint={water_contract_id}&dateFrom={start_dt.isoformat()}&dateTo={end_dt.isoformat()}&intervall=6", headers=header, timeout=10)

        # data in m3, 1 sample / 1 hour
        water_json_data = json.loads(meterdatavalues.content.decode("utf-8"))

        return electrical_json_data, water_json_data

    def logout(self):
        ''' Logout from the SEY '''

        user_element = self._driver.find_element(By.XPATH, "//span[contains(text(),'HJ')]")

        self._screenshot_element(user_element, "user.png")

        ActionChains(self._driver).move_to_element(user_element).click().perform()

        logout = self._driver.find_element(By.XPATH, "//button[contains(text(),'Logout')]")

        self._screenshot_element(logout, "logout.png")

        ActionChains(self._driver).move_to_element(logout).click().perform()

        self._driver.save_screenshot(os.path.join(self._output_folder, "screenshot2.png"))

    def close(self):
        ''' Close the driver '''
        self._driver.quit()

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
        if dt.weekday() in range(0, 4):
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

    def save(self, data_electricity, data_water):
        assert len(data_electricity) == 2

        self._save("energy-production-data-high-tariff.tsv", data_electricity[0]['data'], "sensor:sey_energy_production_high_tariff", "kWh", Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE)
        self._save("energy-production-data-low-tariff.tsv", data_electricity[0]['data'], "sensor:sey_energy_production_low_tariff", "kWh", Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE)
        tariff = (18.10) * 1.081
        self._save("energy-production-cost-high-tariff.tsv", data_electricity[0]['data'], "sensor:sey_energy_production_cost_high_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE, tariff / 100.0)
        tariff = (18.10) * 1.081
        self._save("energy-production-cost-low-tariff.tsv", data_electricity[0]['data'], "sensor:sey_energy_production_cost_low_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE, tariff / 100.0)

        self._save("energy-consumption-data-high-tariff.tsv", data_electricity[1]['data'], "sensor:sey_energy_consumption_high_tariff", "kWh", Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE)
        self._save("energy-consumption-data-low-tariff.tsv", data_electricity[1]['data'], "sensor:sey_energy_consumption_low_tariff", "kWh", Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE)
        tariff = (21.0 + 13.11 + 0.75 + 2.3 + 0.6 + 0.02 + 0.7 + 0.7 + 0.6 + 1.2) * 1.081
        self._save("energy-consumption-cost-high-tariff.tsv", data_electricity[1]['data'], "sensor:sey_energy_consumption_cost_high_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE, tariff / 100.0)
        tariff = (18.75 + 7.56 + 0.75 + 2.3 + 0.6 + 0.02 + 0.7 + 0.7 + 0.6 + 1.2) * 1.081
        self._save("energy-consumption-cost-low-tariff.tsv", data_electricity[1]['data'], "sensor:sey_energy_consumption_cost_low_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE, tariff / 100.0)

        assert len(data_water) == 1

        self._save("water-consumption-data.tsv", data_water[0]['data'], "sensor:sey_water_consumption", "m³", Mode.DATA_NO_BI_TARIFICATION_MODE)
        tariff = (2.95 + 2.30) * 1.081
        self._save("water-consumption-cost.tsv", data_water[0]['data'], "sensor:sey_water_consumption_cost", "CHF/m³", Mode.COST_NO_BI_TARIFICATION_MODE, tariff)

    def _save(self, filename, data, entity_id, unit, mode : Mode, tariff: float = None):
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