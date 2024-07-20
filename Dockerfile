FROM python:3.10-alpine

# update apk repo
RUN echo "http://dl-4.alpinelinux.org/alpine/v3.14/main" >> /etc/apk/repositories && \
    echo "http://dl-4.alpinelinux.org/alpine/v3.14/community" >> /etc/apk/repositories

# install chromedriver
RUN apk update
RUN apk add --no-cache chromium chromium-chromedriver tzdata

ENV TZ=Europe/Zurich

# upgrade pip
RUN pip install --upgrade pip

# install selenium and requests
ADD requirements.txt /
RUN pip install -r /requirements.txt

RUN pip cache purge

# Environment variable for the script execution
ENV SEY_USERNAME=changeme
ENV SEY_PASSWORD=changeme

ENV SEY_ELECTRICAL_CONTRACT_ID=changeme
ENV SEY_WATER_CONTRACT_ID=changeme

ENV DATA_FOLDER=/data

# Copy the module directory and schedule it to be run daily
COPY sey_meter_data_web_scraping/ /usr/local/lib/python3.10/site-packages/
COPY crontab.conf /etc/crontabs/root

# Run cron daemon in frontground
CMD crond -f
