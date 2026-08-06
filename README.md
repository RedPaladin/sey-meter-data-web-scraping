# Web scraping of electric and water meter data from Service des Energies d'Yverdon
Home Assistant add-on (and Docker image) that collects daily electric and water meter data from the [Service des Energies d'Yverdon](https://www.yverdon-energies.ch/).
* Collect the meter data of electric and water from the client portal using [Selenium](https://www.selenium.dev/) and Chromium
* Transform the data into .csv files in order to be imported in Home Assistant using the integration: https://github.com/klausj1/homeassistant-statistics
* Data collection is executed when the add-on/container starts, then continues daily at 3 am while it is running (can be changed by editing `crontab.conf`, but be careful, data may not be available if it is too early). Data are often not available immediately. So the script gets the data from 2 days earlier each day to reduce the risk of missing delayed data.
* Generate files with unique name containing the timestamp of the data collection.
> [!IMPORTANT]  
> The script can be executed only once a day, not more. Because a file containing the total of electricity and water needs to be updated each time the script is executed. The script prevents to be executed two times already.

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
Start the add-on from the Home Assistant UI. Data collection is triggered once at startup, then runs every day at 3 am.

### 6) Home Assistant example to import generated files
To import generated CSV files in Home Assistant, you can use this package example:

https://github.com/RedPaladin/HA_CONFIG/blob/main/packages/sey_import.yaml

What this example provides:

* Template sensors used to expose imported energy/water values in Home Assistant.
* A reusable import script based on `import_statistics.import_from_file`.
* An automation that imports all generated files daily at `03:30:00` (after the add-on run at 3 am).

How to use it:

1. Copy/adapt this package into your Home Assistant `packages` folder (for example `/config/packages/sey_import.yaml`).
2. Ensure package loading is enabled in your Home Assistant configuration.
3. Update the `folder` value in the automation/script so it points to your `data_folder` used by this add-on.
4. Install and configure the Home Assistant integration `homeassistant-statistics` if not already done.

## TODO
- [ ] Create outputs (screenshot, json) generated during execution of the script in a separate folder. Delete it if everything went well.
- [ ] Load the sum data as soon as possible to check if data have been already imported the current day. So we can schedule the execution of the script every hour without accessing to the portal
- [ ] Get automatically the subject id
- [ ] Implement more "aggressive" scheduling after capabilities check. Days -2 before at 1am!
- [ ] Add DEBUG mode to optionally export JSON format from SEY API
