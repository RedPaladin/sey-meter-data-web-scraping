#!/usr/bin/with-contenv sh
set -e

python3 -m sey_meter_data_web_scraping || crond -f
