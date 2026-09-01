# Web scraping of electric and water meter data from Service des Energies d'Yverdon
Home Assistant add-on (and Docker image) that collects daily electric and water meter data from the [Service des Energies d'Yverdon](https://www.yverdon-energies.ch/).
* Collect the meter data of electric and water from the client portal using [Selenium](https://www.selenium.dev/) and Chromium
* Transform the data into .csv files in order to be imported in Home Assistant using the integration: https://github.com/klausj1/homeassistant-statistics
* Data collection is executed when the add-on/container starts, then continues every hour while it is running (can be changed by editing `crontab.conf`). Data are often not available immediately. So the script gets the data from 7 days earlier each day to reduce the risk of missing delayed data.
* Generate files with unique name containing the timestamp of the data collection.
* Each generated file reports per-interval consumption deltas, so the script can safely be re-executed for the same day (it simply regenerates that day's files) without any risk of double-counting.

## Home Assistant add-on installation (recommended)

### 1) Clone this repository into your Home Assistant add-ons directory
```bash
cd /addons
git clone https://github.com/RedPaladin/sey-meter-data-web-scraping.git
```

### 2) Restart Home Assistant
After cloning, restart Home Assistant so the new local add-on is detected.

### 3) Install the add-on
Go to **Settings > Add-ons > Add-on Store > Local add-ons**, open this add-on, then click **Install**.

### 4) Configure the add-on
Set the following options in the add-on configuration:

| Option | Description |
| --- | --- |
| sey_username | Username to login into client portal |
| sey_password | Password to login into client portal |
| sey_subject_id | Subject ID given by SEY |
| sey_electrical_contract_id | ID of your electrical contract (get it on your client portal) |
| sey_water_contract_id | ID of your water contract (get it on your client portal) |
| data_folder | Location where to store the data (default: /config/sey_meter_data_web_scraping) |

This add-on requires `homeassistant_api: true` (already set in `config.yaml`) so it can read electricity and water tariffs from Home Assistant sensors via the Supervisor API, instead of having them hardcoded. Make sure the following sensors exist in your Home Assistant instance before starting the add-on:

| Sensor entity | Expected unit |
| --- | --- |
| sensor.electricity_price_consumption_high_tariff | ct/kWh |
| sensor.electricity_price_consumption_low_tariff | ct/kWh |
| sensor.electricity_price_returned_to_grid_tariff | ct/kWh |
| sensor.water_price_consumption_tariff | CHF/m³ |

Example configuration:

```yaml
sey_username: "your_username"
sey_password: "your_password"
sey_subject_id: "your_subject_id"
sey_electrical_contract_id: "your_electrical_contract_id"
sey_water_contract_id: "your_water_contract_id"
data_folder: "/config/sey_meter_data_web_scraping"
```

This add-on supports these Home Assistant architectures: `aarch64`, `amd64`, `armhf`, `armv7`, `i386`.

### 5) Start the add-on
Start the add-on from the Home Assistant UI. Data collection is every hour.

### 6) Home Assistant example to import generated files
To import generated CSV files in Home Assistant, you can use this package example:

https://github.com/RedPaladin/HA_CONFIG/blob/main/packages/sey_import.yaml

What this example provides:

* Template sensors used to expose imported energy/water values in Home Assistant.
* A reusable import script based on `import_statistics.import_from_file`.
* An automation that imports all generated files (this may need to be adjusted based on your data availability and collection timing).

How to use it:

1. Copy/adapt this package into your Home Assistant `packages` folder (for example `/config/packages/sey_import.yaml`).
2. Ensure package loading is enabled in your Home Assistant configuration.
3. Update the `folder` value in the automation/script so it points to your `data_folder` used by this add-on.
4. Install and configure the Home Assistant integration `homeassistant-statistics` if not already done.

## TODO
- [ ] Create outputs (screenshot, json) generated during execution of the script in a separate folder. Delete it if everything went well.
- [ ] Get automatically the subject id
