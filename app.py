#!/usr/bin/env python3

import os
import sys
import subprocess
import datetime

from flask import Flask, render_template, request, redirect, url_for, make_response

# import logging
import sentry_sdk
from sentry_sdk.integrations.flask import (
    FlaskIntegration,
)  # delete this if not using sentry.io

# from markupsafe import escape
import pymongo
from pymongo.errors import ConnectionFailure
from bson.objectid import ObjectId
from dotenv import load_dotenv

# load credentials and configuration options from .env file
# if you do not yet have a file named .env, make one based on the template in env.example
load_dotenv(override=True)  # take environment variables from .env.

# initialize Sentry for help debugging... this requires an account on sentrio.io
# you will need to set the SENTRY_DSN environment variable to the value provided by Sentry
# delete this if not using sentry.io
sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    # enable_tracing=True,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    # We recommend adjusting this value in production.
    integrations=[FlaskIntegration()],
    send_default_pii=True,
)

# instantiate the app using sentry for debugging
app = Flask(__name__)

# # turn on debugging if in development mode
# app.debug = True if os.getenv("FLASK_ENV", "development") == "development" else False

# try to connect to the database, and quit if it doesn't work
try:
    cxn = pymongo.MongoClient("mongodb+srv://lw2808:KhzRIPszwosrZQoD@cluster0.jizlbho.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0&tlsCAFile=isrgrootx1.pem")
    db = cxn["lw2808"]  # store a reference to the selected database

    # verify the connection works by pinging the database
    print(" * Connected to MongoDB!")  # if we get here, the connection worked!
except ConnectionFailure as e:
    # catch any database errors
    # the ping command failed, so the connection is not available.
    print(" * MongoDB connection error:", e)  # debug
    sentry_sdk.capture_exception(e)  # send the error to sentry.io. delete if not using
    sys.exit(1)  # this is a catastrophic error, so no reason to continue to live


# set up the routes
@app.route("/")
def home():
    """
    Route for the home page.
    Simply returns to the browser the content of the index.html file located in the templates folder.
    """
    return render_template("index.html")


@app.route("/read")
def read():
    """
    Route for GET requests to the read page.
    Displays some information for the user with links to other pages.
    """
    hotels = db.hotels.find({"city": "New York City"}).sort(
        "rating", -1
        )
    return render_template("read.html", hotels=hotels) # render the read template


@app.route("/create", methods=["GET", "POST"])
def create_hotel():
    """
    Route for GET requests to the create page.
    Displays a form users can fill out to create a new document.
    Route for POST requests to the create page.
    Accepts the form submission data for a new document and saves the document to the database.
    """
    if request.method == 'GET':
        return render_template('create.html')
    
    elif request.method == "POST":
        name = request.form["name"]
        city = "New York City"
        rating = int(request.form["rating"])
        address = request.form["address"]
        
        hotel = {
            "name": name,
            "city": city,
            "rating": rating,
            "address": address
        }
        db.hotels.insert_one(hotel)
        return redirect(url_for("read"))


@app.route("/edit/<hotel_id>", methods=["GET", "POST"])
def edit(hotel_id):
    """
    Route for GET requests to the edit page.
    Displays a form users can fill out to edit an existing record.
    """

    hotel_updated = db.hotels.find_one({"_id": ObjectId(hotel_id), "city": "New York City"})

    if request.method == 'GET':
        return render_template('edit.html', hotel=hotel_updated)
    
    elif request.method == "POST":
        name = request.form["name"]
        rating = int(request.form["rating"])
        address = request.form["address"]
        
        updated = {
            "name": name,
            "rating": rating,
            "address": address
        }
        db.hotels.update_one({"_id": ObjectId(hotel_id)}, {"$set": updated})
        return redirect(
            url_for("read", hotel_id=hotel_id)
            )


@app.route("/delete/<hotel_id>")
def delete(hotel_id):
    """
    Route for GET requests to the delete page.
    Deletes the specified record from the database, and then redirects the browser to the read page.
    """
    db.hotels.delete_one({"_id": ObjectId(hotel_id), "city": "New York City"})
    return redirect(
        url_for("home")
        )


@app.errorhandler(Exception)
def handle_error(e):
    """
    Output any errors - good for debugging.
    """
    return render_template("error.html", error=e)  # render the edit template


# run the app
if __name__ == "__main__":
    # logging.basicConfig(filename="./flask_error.log", level=logging.DEBUG)
    app.run(load_dotenv=True)