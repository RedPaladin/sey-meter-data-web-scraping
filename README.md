# Web scraping of electric and water meter data from Service des Energies d'Yverdon
Docker image thats collects daily the electric and water meter data from the [Service des Energies d'Yverdon](https://www.yverdon-energies.ch/)
* Collect the meter data of electric and water from the client portal using [Selenium](https://www.selenium.dev/) and Chromium
* Transform the data into .csv files in order to be imported in Home Assistant using the integration: https://github.com/klausj1/homeassistant-statistics
* Data collection is done daily at 12 pm while the container is running (can be changed by editing crontab.conf but be careful, data may not be available if it is too early). Data are often not available, sometimes only 3 days after. So the script get the data 3 days before every day to ensure not losing data.
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
| SEY_SUBJECT_ID | Subject ID given by SEY |
| SEY_ELECTRICAL_CONTRACT_ID | ID of your electrical contract (get it on your client portal) |
| SEY_WATER_CONTRACT_ID | ID of your water contract (get it on your client portal) |
| DATA_FOLDER | Location where to store the data. Bind a folder with your host |

## Build the docker image locally
`docker build . -t redpaladin751/sey-meter-data-web-scraping`

### Run the docker image
`docker run --rm -it -e SEY_USERNAME=changeme -e SEY_PASSWORD=changeme -e SEY_SUBJECT_ID=changeme -e SEY_ELECTRICAL_CONTRACT_ID=changeme -e SEY_WATER_CONTRACT_ID=changeme -e DATA_FOLDER=/data --mount type=bind,src=./data,dst=/data redpaladin751/sey-meter-data-web-scraping`

## Work without docker

### Run the test
`SEY_USERNAME=changeme SEY_PASSWORD=changeme SEY_SUBJECT_ID=changeme SEY_ELECTRICAL_CONTRACT_ID=changeme SEY_WATER_CONTRACT_ID=changeme python -m unittest discover -v`

### Run the package
`SEY_USERNAME=changeme SEY_PASSWORD=changeme SEY_SUBJECT_ID=changeme SEY_ELECTRICAL_CONTRACT_ID=changeme SEY_WATER_CONTRACT_ID=changeme DATA_FOLDER=data python -m sey_meter_data_web_scraping`

## TODO
- [ ] Use template sensor (template_value: None and StateClass set to TOTAL_INCREASE) to display friendly name in HA
- [ ] Create outputs (screenshot, json) generated during execution of the script in a separate folder. Delete it if everything went well.
- [ ] Load the sum data as soon as possible to check if data have been already imported the current day. So we can schedule the execution of the script every hour without accessing to the portal
- [ ] Get automatically the subject id
- [ ] Implement more "aggressive" scheduling after capabilities check. Days -2 before at 1am!
- [ ] Transfer credentials to .env instead of environment variables (more secure)
- [ ] Add DEBUG mode to optionally export JSON format from SEY API
