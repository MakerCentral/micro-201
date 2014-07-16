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
import ctypes

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
POST_FREQ       = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
UPDATE_FREQ     = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
DEV_NAME        = sys.argv[1] if len(sys.argv) > 1 else "Raspberry Pi"
STATUS          = "[{0}] Temperature: {1:.2f} °C, Humidity: {2:.2f} %" 

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

# Read the sensor value
def read_sensor(v, sensor):
    try:
        while True:
            v.t = t = sensor.temperature
            v.h = h = sensor.humidity
            v.u = True
            
            write_lock.acquire()
            print "UPDATE: {0}, {1}".format(t, h)
            write_lock.release()

            time.sleep(UPDATE_FREQ)
    except KeyboardInterrupt: pass

def post_update(v, twitter):
    try:
        while True:
            # Check for updates
            if v.u:
                # Clear the update
                v.u = False

                # Generate the status tweet
                msg = STATUS.format(DEV_NAME, v.t, v.h)
                
                # Output the status to the console 
                write_lock.acquire()
                print "STATUS: {0}".format(msg)
                write_lock.release()

                # Post to twitter
                twitter.update_status(msg)
            
                # Delay to update on a regular interval
                time.sleep(POST_FREQ)

    # Handle exceptions
    except KeyboardInterrupt: pass
    except Exception, ex:
        if not isinstance(ex, tweepy.TweepError) or re.search('duplicate', ex.reason) is None:
            write_lock.acquire()
            print "ERROR: {0}".format(ex)
            write_lock.release()
            
# Create a ctype for sensor state (shared memory object)
class Status(ctypes.Structure):
    _fields_ = [('t', ctypes.c_double), ('h', ctypes.c_double), ('u', ctypes.c_bool)]

# Initialize the system
try:
    value   = multiprocessing.Value(Status, lock=True)
    sensor  = init_sensor()
    twitter = init_twitter()

    # Define sub-tasks as sub-processes
    p1 = multiprocessing.Process(target=read_sensor, args=(value, sensor))
    p2 = multiprocessing.Process(target=post_update, args=(value, twitter))

    # Start subprocesses
    p1.start()
    p2.start()

    # Block the main thread
    p1.join()
    p2.join()

except KeyboardInterrupt: pass            

# Exit the application cleanly
sys.exit(0)
