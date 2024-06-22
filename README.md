# Web scraping of electric and water meter data from Service des Energies d'Yverdon
Docker image thats collects daily the electric and water meter data from the [Service des Energies d'Yverdon](https://www.yverdon-energies.ch/)
* Collect the meter data of electric and water from the client portal using [Selenium](https://www.selenium.dev/) and Chromium
* Transform the data into .csv files in order to be imported in Home Assistant using the integration: https://github.com/klausj1/homeassistant-statistics
* Data collection is done daily at 6 am (can be changed by editing crontab.conf) while the container is runing. The data are available only the day after, not in live. An unique filename is generated using the timestamp of the data.

## Get the docker image
`docker pull redpaladin751/sey-meter-data-web-scraping:latest`

## Build the docker image
`docker build . -t redpaladin751/sey-meter-data-web-scraping`

Set following environment variables
| Variable | Description |
| --- | --- |
| SEY_USERNAME | Username to login into client portal |
| SEY_PASSWORD | Password to login into client portal |
| SEY_ELECTRICAL_CONTRACT_ID | ID of your electrical contract (get it on your client portal) |
| SEY_WATER_CONTRACT_ID | ID of your water contract (get it on your client portal) |
| DATA_FOLDER | Location where to store the data. Bind a folder with your host |

## TODO
- [x] Convert JSON from API to CSV for HASS service import integrations
- [ ] Use electrical data with 15 min period instead of 1 hour