#!/usr/bin/env python3

import json
import os
from datetime import datetime, timedelta

import requests
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

class SeyWebScraper:
    ''' Class to Web Scrap from SEY '''

    def __init__(self):
        chrome_options = webdriver.ChromeOptions()

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument("--window-size=1920,1080")

        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        self._driver = webdriver.Chrome(options=chrome_options)
        self._driver.implicitly_wait(20)

    def _screenshot_element(self, elem, filename):
        with open(filename, "wb") as f:
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

        #print(self._driver.get_cookies())

        username_element = self._driver.find_element(By.ID, "username")

        username_element.send_keys(username)

        self._screenshot_element(username_element, "username.png")

        password_element = self._driver.find_element(By.ID, "password")

        password_element.send_keys(password)

        self._screenshot_element(password_element, "password.png")

        self._driver.save_screenshot("screenshot0.png")

        sign_in = self._driver.find_element(By.ID, "kc-login")
        
        ActionChains(self._driver).move_to_element(sign_in).click().perform()

        #print(self._driver.get_cookies())

        self._driver.save_screenshot("screenshot1.png")

    def collect(self, electrical_contract_id, water_contract_id, date, folder):
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

        self._driver.save_screenshot("screenshot2.png")

    def close(self):
        ''' Close the driver '''
        self._driver.quit()

class SeyDataSaver:
    def __init__(self) -> None:
        pass

    def _extract_data(self, data, entity_id, unit):
        # print the headers
        yield "statistic_id\tunit\tstart\tmin\tmax\tmean"
        for d in data:
            dt = d['x']
            cons = d['y']

            dt = datetime.fromisoformat(dt) - timedelta(hours=1)
            dt = dt.strftime("%d.%m.%Y %H:%M")

            yield f"{entity_id}\t{unit}\t{dt}\t{cons:.3f}\t{cons:.3f}\t{cons:.3f}"

    def _save_data(self, filename, generator):
        with open(filename, "w", encoding="utf-8") as f:
            print(f"Saving file: {filename}")
            for line in generator:
                #print(line)
                f.write(line + "\n")

    def save(self, filename, data, entity_id, unit):
        self._save_data(filename, self._extract_data(data, entity_id, unit))


USERNAME = os.getenv("SEY_USERNAME")
PASSWORD = os.getenv("SEY_PASSWORD")

ELECTRICAL_CONTRACT_ID = os.getenv("SEY_ELECTRICAL_CONTRACT_ID")
WATER_CONTRACT_ID = os.getenv("SEY_WATER_CONTRACT_ID")

DATA_FOLDER = os.getenv("DATA_FOLDER")

scrapper = SeyWebScraper()

try:
    scrapper.login(USERNAME, PASSWORD)
    dt = datetime.now() - timedelta(days = 1)
    electrical_json_data, water_json_data = scrapper.collect(ELECTRICAL_CONTRACT_ID, WATER_CONTRACT_ID, dt, DATA_FOLDER)
    scrapper.logout()

    saver = SeyDataSaver()

    saver.save(os.path.join(DATA_FOLDER, dt.strftime("%Y%m%d") + "-power-production-data.tsv"), electrical_json_data[0]['data'], "sensor:sey_power_production", "kWh")
    saver.save(os.path.join(DATA_FOLDER, dt.strftime("%Y%m%d") + "-power-consumption-data.tsv"), electrical_json_data[1]['data'], "sensor:sey_power_consumption", "kWh")
    saver.save(os.path.join(DATA_FOLDER, dt.strftime("%Y%m%d") + "-water-consumption-data.tsv"), water_json_data[0]['data'], "sensor:sey_water_consumption", "m³")
finally:
    scrapper.close()
