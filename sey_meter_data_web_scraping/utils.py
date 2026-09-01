import json
import os
from datetime import datetime, timedelta
from enum import Enum

import requests

from selenium import webdriver
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WAIT_TIMEOUT = 20  # Default timeout in seconds for all WebDriverWait calls

class SeyWebScraper:
    ''' Class to Web Scrap from SEY '''

    def __init__(self, output_folder):

        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")

        self._user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        chrome_options.add_argument(f'--user-agent={self._user_agent}')

        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        self._driver = webdriver.Chrome(options=chrome_options)
        # No implicit wait: all element lookups use explicit WebDriverWait below.
        # Mixing implicit and explicit waits makes Selenium's polling/timeout
        # behavior unpredictable.
        self._output_folder = output_folder

        assert os.path.exists(self._output_folder)

    def _screenshot_element(self, elem, filename):
        with open(os.path.join(self._output_folder, filename), "wb") as f:
            f.write(elem.screenshot_as_png)

    def _on_wait_failure(self, selector, attempt):
        error_filename = f"error_attempt{attempt}_{''.join(c if c.isalnum() else '_' for c in selector)}.png"
        self._driver.save_screenshot(os.path.join(self._output_folder, error_filename))

    def _safe_click(self, by, selector, filename=None, timeout=WAIT_TIMEOUT, retries=3):
        for attempt in range(1, retries + 1):
            try:
                element = WebDriverWait(self._driver, timeout).until(
                    EC.element_to_be_clickable((by, selector))
                )
                if filename:
                    self._screenshot_element(element, filename)
                element.click()
                return
            except (StaleElementReferenceException, TimeoutException):
                if attempt == retries:
                    self._on_wait_failure(selector, attempt)
                    raise

    def _safe_send_keys(self, by, selector, keys, filename=None, timeout=WAIT_TIMEOUT, retries=3):
        for attempt in range(1, retries + 1):
            try:
                element = WebDriverWait(self._driver, timeout).until(
                    EC.presence_of_element_located((by, selector))
                )
                if filename:
                    self._screenshot_element(element, filename)
                element.clear()
                element.send_keys(keys)
                return
            except (StaleElementReferenceException, TimeoutException):
                if attempt == retries:
                    self._on_wait_failure(selector, attempt)
                    raise

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
        print("Login into SEY")

        self._driver.get("https://my.yverdon-energies.ch/login")

        self._safe_click(By.XPATH, "//span[text()='Se connecter ici']/ancestor::button", "login.png")

        self._safe_send_keys(By.ID, "username", username, "username.png")
        self._safe_send_keys(By.ID, "password", password, "password.png")

        self._driver.save_screenshot(os.path.join(self._output_folder, "screenshot0.png"))

        self._safe_click(By.ID, "kc-login")

    def collect(self, electrical_contract_id, water_contract_id, subject_id, date):
        print("Collect the data from the SEY")

        # Wait until this element is visible so we are sure the keycloak session is open
        wait = WebDriverWait(self._driver, WAIT_TIMEOUT)
        wait.until(
            EC.visibility_of_element_located((By.XPATH, "//div[normalize-space(text())='Contrats']"))
        )
        
        self._driver.save_screenshot(os.path.join(self._output_folder, "screenshot1.png"))

        # Get the authorization from the Chrome log (this is all the magic comes from!)
        logs = self._driver.get_log("performance")

        header = self._get_authorization_token_id(logs)
        header["User-Agent"] = self._user_agent

        start_dt = datetime.combine(date, datetime.min.time())
        end_dt = datetime.combine(datetime.now() + timedelta(days = 1), datetime.min.time()) - timedelta(minutes = 1)

        meterdatavalues = requests.get(f"https://my.yverdon-energies.ch/ebpapi/ebp/meterdatavalues/{electrical_contract_id}?subject_id={subject_id}&role=1&date_from={start_dt.isoformat()}&date_to={end_dt.isoformat()}&aggregation=2&compareActive=false", headers=header, timeout=10)

        # data in kWh, 1 sample / 1 hour
        electrical_json_data = json.loads(meterdatavalues.content.decode("utf-8"))
        
        self._save_json(f"electrical_data_{date.strftime('%Y%m%d')}.json", electrical_json_data)

        # seems to work only with data from yesterday, not older. Why ?
        meterdatavalues = requests.get(f"https://my.yverdon-energies.ch/ebpapi/ebp/meterdatavalues/{water_contract_id}?subject_id={subject_id}&role=1&date_from={start_dt.isoformat()}&date_to={end_dt.isoformat()}&aggregation=2&compareActive=false", headers=header, timeout=10)

        # data in m3, 1 sample / 1 hour
        water_json_data = json.loads(meterdatavalues.content.decode("utf-8"))

        self._save_json(f"water_json_data_{date.strftime('%Y%m%d')}.json", water_json_data)

        return electrical_json_data, water_json_data
    
    def _save_json(self, filename, data):
        ''' Save the JSON data to a file '''

        with open(os.path.join(self._output_folder, filename), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Save json: {filename}")

    def logout(self):
        print("Logout from the SEY")

        self._safe_click(By.XPATH, "//mat-icon[text()='person']/ancestor::button", "user.png")
        self._safe_click(By.XPATH, "//mat-icon[text()='logout']/ancestor::button", "logout.png")

        self._driver.save_screenshot(os.path.join(self._output_folder, "screenshot2.png"))

    def close(self):
        ''' Close the driver '''
        self._driver.quit()

        print("Done! See you tomorrow!")

class Mode(Enum):
    DATA_NO_BI_TARIFICATION_MODE = 0
    COST_NO_BI_TARIFICATION_MODE = 1
    DATA_BI_TARIFICATION_HIGH_TARIFF_MODE = 2
    DATA_BI_TARIFICATION_LOW_TARIFF_MODE = 3
    COST_BI_TARIFICATION_HIGH_TARIFF_MODE = 4
    COST_BI_TARIFICATION_LOW_TARIFF_MODE = 5

class SeyDataSaver:
    def __init__(self, folder, dt) -> None:
        self._folder = folder
        self._date = dt.strftime("%Y%m%d")

    def _is_high_tariff_datetime(self, dt : datetime) -> bool:
        if dt.weekday() in range(0, 4):
            return dt.hour >= 6 and dt.hour < 22
        else: # weekend
            return (dt.hour >= 10 and dt.hour < 13) or (dt.hour >= 17 and dt.hour < 22)

    def _extract_data(self, data, entity_id, unit, mode : Mode, tariff: float = None):
        # print the headers
        yield "statistic_id\tunit\tstart\tdelta"

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

            yield f"{entity_id}\t{unit}\t{dt}\t{(state):.3f}"

    def _save_data(self, filename, generator):
        with open(filename, "w", encoding="utf-8") as f:
            print(f"Saving file: {filename}")
            for line in generator:
                #print(line)
                f.write(line + "\n")

    def save(self, data_electricity, data_water, prices):

        data_electricity = data_electricity['timeseries']

        if len(data_electricity) < 1:
            print("ERROR: No data for production of electricity found")

        else:
            print("Saving data of production of electricity")
            self._save("energy-production-data-high-tariff.tsv", data_electricity[0]['data'], "sensor.sey_energy_returned_to_grid_high_tariff", "kWh", Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE)
            self._save("energy-production-data-low-tariff.tsv", data_electricity[0]['data'], "sensor.sey_energy_returned_to_grid_low_tariff", "kWh", Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE)
            tariff = prices["electricity_returned_to_grid_tariff"]
            self._save("energy-production-cost-high-tariff.tsv", data_electricity[0]['data'], "sensor.sey_cost_energy_returned_to_grid_high_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE, tariff)
            self._save("energy-production-cost-low-tariff.tsv", data_electricity[0]['data'], "sensor.sey_cost_energy_returned_to_grid_low_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE, tariff)

        if len(data_electricity) < 2:
            print("ERROR: No data for consumption of electricity found")

        else:
            print("Saving data of consumption of electricity")
            self._save("energy-consumption-data-high-tariff.tsv", data_electricity[1]['data'], "sensor.sey_energy_consumption_high_tariff", "kWh", Mode.DATA_BI_TARIFICATION_HIGH_TARIFF_MODE)
            self._save("energy-consumption-data-low-tariff.tsv", data_electricity[1]['data'], "sensor.sey_energy_consumption_low_tariff", "kWh", Mode.DATA_BI_TARIFICATION_LOW_TARIFF_MODE)
            tariff = prices["electricity_consumption_high_tariff"]
            self._save("energy-consumption-cost-high-tariff.tsv", data_electricity[1]['data'], "sensor.sey_cost_energy_consumption_high_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_HIGH_TARIFF_MODE, tariff)
            tariff = prices["electricity_consumption_low_tariff"]
            self._save("energy-consumption-cost-low-tariff.tsv", data_electricity[1]['data'], "sensor.sey_cost_energy_consumption_low_tariff", "CHF/kWh", Mode.COST_BI_TARIFICATION_LOW_TARIFF_MODE, tariff)

        data_water = data_water['timeseries']

        if len(data_water) < 1:
            print("ERROR: No data for consumption of water found")

        else:
            print("Saving data of water consumption")
            self._save("water-consumption-data.tsv", data_water[0]['data'], "sensor.sey_water_consumption", "m³", Mode.DATA_NO_BI_TARIFICATION_MODE)
            tariff = prices["water_consumption_tariff"]
            self._save("water-consumption-cost.tsv", data_water[0]['data'], "sensor.sey_water_cost", "CHF/m³", Mode.COST_NO_BI_TARIFICATION_MODE, tariff)

    def _save(self, filename, data, entity_id, unit, mode : Mode, tariff: float = None):
        full_filename = os.path.join(self._folder, f"{self._date}-{filename}")

        self._save_data(full_filename, self._extract_data(data, entity_id, unit, mode, tariff))
