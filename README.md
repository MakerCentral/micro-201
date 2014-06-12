# Microprocessor 201

## Project: Tweet-o-stat
---
Creates a twitter based thermostat that outputs temperature and humidity
readings of a HTU21D connected to a raspberry pi. Handles all
authentication and communication with the twitter API and the sensor.

## Getting started
---

This project uses python virtualenv to manage its dependencies. Run the 
script:

    ./init.sh

to set up the environment (**THIS REQUIRES INTERNET ACCESS**). Then, enter
the environment using the activate script:

    source venv/bin/activate

The prompt will change to reflect the activated virtual environment. To
exit the environment, run:

    deactivate

## Running the program
---

To run the project, invoke the main script directly:

    ./tweet-o-stat.py

or via the python interpreter:

    python tweet-o-stat.py

## Usage
---

    ./tweet-o-stat.py <POST_INTERVAL> <UPDATE_INTERVAL>

The program takes two optional arguments:

    <POST_INTERVAL>   - The time in seconds between tweets. Supports floating point for sub-second resolution.
    <UPDATE_INTERVAL> - The time in seconds between sensor updates. Supports floating point for sub-second resolution.

These parameters have sane defaults of 60 and 1 when not used. It is not
recommended to post more frequently than every 5 seconds, and update more
frequently than 1 second.

## Authentication
---

This program handles authentication via PIN and twitter OAuth. On first run,
the program will automatically open a browser at the login page of twitter
to request a PIN. Copy the PIN after logging in and paste it into the
prompt. The resulting credentials are cached in a file called 
`.twitter_auth` for future use. If you would like to clear your
credentials, delete this file.
