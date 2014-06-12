#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Core python libraries
import re
import os
import sys
import time
import math
import random
import webbrowser
import multiprocessing

# Twitter python binding
import tweepy

# HTU21D driver
import htu21d

#####################################################################
# CONFIGURATION
#####################################################################

TWITTER_FILE    = ".twitter_auth"
CONSUMER_TOKEN  = "7BUWu047EIfcLy3rUWd9v0L56"
CONSUMER_SECRET = "M63zg1GFcNsaIK1U8zEpcmNm11RuHJlAGuUrIuGOi6pTdJarEw"
POST_FREQ       = int(sys.argv[1]) if len(sys.argv) > 1 else 60
UPDATE_FREQ     = int(sys.argv[2]) if len(sys.argv) > 2 else 1
STATUS          = "[Raspberry Pi] Temperature: {0:.2f} °C, Humidity: {1:.2f} %" 

#####################################################################
# CODE 
#####################################################################

write_lock  = multiprocessing.Lock()

def init_twitter():
    # Create authorization using the application identifiers
    print "Initializing connecting to twitter"
    auth = tweepy.OAuthHandler(CONSUMER_TOKEN, CONSUMER_SECRET)
    
    # Load credentials from file cache
    if os.path.exists(TWITTER_FILE):
        print "Loading auth from cache..."
        data = None
        with open(TWITTER_FILE) as f:
            data = f.readlines()
        data = [d.strip() for d in data]

        # Populate authorization from saved credentials
        auth.set_access_token(*data)
    
    # Request credentials from twitter via PIN
    else:
        # Open the system browser at the authorization URL
        url = auth.get_authorization_url()
        print "Authentication Requred - Log into twitter"
        webbrowser.open(url)
        
        # Request the authorization PIN
        code = raw_input("Authorization PIN (Press <ENTER> when done): ")
        auth.get_access_token(code)

        # Cache the authorization codes for future use
        print "Caching credentials for future use..."
        with open(TWITTER_FILE, "w") as f:
            f.write(auth.access_token.key + "\n")
            f.write(auth.access_token.secret)

    # Return the twitter API handle
    return tweepy.API(auth)

# Initialize and return any relevant sensor information
def init_sensor():
    return htu21d.HTU21D()

def read_sensor(q, sensor):
    try:
        while True:
            t = sensor.temperature
            h = sensor.humidity
            #t = float(random.randint(30,50))
            #h = round(random.random() * 100.0,2)
            q.put((t, h))
            
            write_lock.acquire()
            print "UPDATE: {0}, {1}".format(t, h)
            write_lock.release()

            time.sleep(UPDATE_FREQ)

    # Handle close edge case
    except KeyboardInterrupt: pass

def post_update(q, twitter):
    try:
        while True:
            # Generate the status tweet
            msg = STATUS.format(*(q.get()))
            
            # Output the status to the console 
            write_lock.acquire()
            print "STATUS: {0}".format(msg)
            write_lock.release()

            # Post to twitter
            twitter.update_status(msg)
            
            # Delay to update on a regular interval
            time.sleep(POST_FREQ)

    # Handle edge cases and exceptions
    except KeyboardInterrupt: pass
    except Exception, ex:
        if not isinstance(ex, tweepy.TweepError) or re.search('duplicate', ex.reason) is None:
            write_lock.acquire()
            print "ERROR: {0}".format(ex)
            write_lock.release()
            

# Initialize the system
queue   = multiprocessing.Queue()
sensor  = init_sensor()
twitter = init_twitter()

# Define sub-tasks as sub-processes
p1 = multiprocessing.Process(target=read_sensor, args=(queue, sensor))
p2 = multiprocessing.Process(target=post_update, args=(queue, twitter))

# Start subprocesses
p1.start()
p2.start()

# Block the main thread
try:
    raw_input()
except KeyboardInterrupt: pass            

# Stop subprocesses
p1.join()
p2.join()

# Exit the application cleanly
sys.exit(0)
