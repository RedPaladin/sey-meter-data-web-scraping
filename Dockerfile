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
RUN pip install selenium requests

RUN pip cache purge

# Environment variable for the script execution
ENV SEY_USERNAME=changeme
ENV SEY_PASSWORD=changeme

ENV SEY_ELECTRICAL_CONTRACT_ID=changeme
ENV SEY_WATER_CONTRACT_ID=changeme

ENV DATA_FOLDER=/data

# Copy the script and schedule it daily
COPY collect_meterdatavalues.py /
COPY crontab.conf /etc/crontabs/root

# Run cron daemon in frontground
CMD crond -f