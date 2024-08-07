# Web scraping of electric and water meter data from Service des Energies d'Yverdon
Docker image thats collects daily the electric and water meter data from the [Service des Energies d'Yverdon](https://www.yverdon-energies.ch/)
* Collect the meter data of electric and water from the client portal using [Selenium](https://www.selenium.dev/) and Chromium
* Transform the data into .csv files in order to be imported in Home Assistant using the integration: https://github.com/klausj1/homeassistant-statistics
* Data collection is done daily at 10 am while the container is running (can be changed by editing crontab.conf but be careful, data may not be available if it is too early). The data can be collected only the day after, not in live, so this is why the script collects only the data from the day before.
* Generate files with unique name containing the timestamp of the data collection.
> [!IMPORTANT]  
> The script can be executed only once a day, not more. Because a file containing the total of electricity and water needs to be updated each time the script is executed. The script prevents to be executed two times already.

## Get the docker image from DockerHub (preferred solution ❤️)
`docker pull redpaladin751/sey-meter-data-web-scraping:latest`

### Set following environment variables
| Variable | Description |
| --- | --- |
| SEY_USERNAME | Username to login into client portal |
| SEY_PASSWORD | Password to login into client portal |
| SEY_ELECTRICAL_CONTRACT_ID | ID of your electrical contract (get it on your client portal) |
| SEY_WATER_CONTRACT_ID | ID of your water contract (get it on your client portal) |
| DATA_FOLDER | Location where to store the data. Bind a folder with your host |

## Build the docker image locally
`docker build . -t redpaladin751/sey-meter-data-web-scraping`

### Run the docker image
`docker run --rm -it -e SEY_USERNAME=changeme -e SEY_PASSWORD=changeme -e SEY_ELECTRICAL_CONTRACT_ID=changeme -e SEY_WATER_CONTRACT_ID=changeme -e DATA_FOLDER=/data --mount type=bind,src=./data,dst=/data redpaladin751/sey-meter-data-web-scraping`

## Work without docker

### Run the test
`SEY_USERNAME=changeme SEY_PASSWORD=changeme SEY_ELECTRICAL_CONTRACT_ID=changeme SEY_WATER_CONTRACT_ID=changeme python -m unittest discover -v`

### Run the package
`SEY_USERNAME=changeme SEY_PASSWORD=changeme SEY_ELECTRICAL_CONTRACT_ID=changeme SEY_WATER_CONTRACT_ID=changeme DATA_FOLDER=data python -m sey_meter_data_web_scraping`

## TODO
- [x] Convert JSON from API to CSV for HASS service import integrations
- [x] Save the sums in a smarter way (if you execute the script twice)
- [x] Rename output files with energy
- [ ] Use Name field in hass db to set a friendly name to the sensors
- [x] Generate cost report based on PDF's [electricity](EL-Tarifs-simplifie-2024.pdf) and [water](D-SERV-02-07-Tarif-eau.pdf)
- [x] Automate building of Docker image with GitHub Actions
- [ ] Improve logout of the client portal
- [ ] Improve logging
- [ ] Delete older data before generating new ones
