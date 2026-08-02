ARG BUILD_FROM=ghcr.io/home-assistant/base-python:3.14-alpine3.24
FROM ${BUILD_FROM}

# install chromedriver
RUN apk update && \
    apk add --no-cache chromium chromium-chromedriver tzdata

ENV TZ=Europe/Zurich

# upgrade pip
RUN python3 -m pip install --upgrade pip

# install selenium and requests
ADD requirements.txt /
RUN python3 -m pip install -r /requirements.txt

#RUN python3 -m pip cache purge

# Environment variable for the script execution
ENV SEY_USERNAME=changeme
ENV SEY_PASSWORD=changeme
ENV SEY_SUBJECT_ID=changeme

ENV SEY_ELECTRICAL_CONTRACT_ID=changeme
ENV SEY_WATER_CONTRACT_ID=changeme

ENV DATA_FOLDER=/homeassistant/data
ENV PYTHONPATH=/app

# Copy the module directory and schedule it to be run daily
COPY sey_meter_data_web_scraping /app/sey_meter_data_web_scraping
COPY crontab.conf /etc/crontabs/root

# Ensure package is available in site-packages so python3 -m can import it
RUN python3 - <<'PY'
import site, shutil, os
src = '/app/sey_meter_data_web_scraping'
dst = site.getsitepackages()[0] + '/sey_meter_data_web_scraping'
if os.path.exists(src) and not os.path.exists(dst):
    shutil.copytree(src, dst)
PY

# Run cron daemon in foreground
CMD python3 -m sey_meter_data_web_scraping || crond -f
