import json
from datetime import datetime
import time
from calendar import timegm
from math import floor

from skyfield.api import Topos, load, utc

from flask import Flask, jsonify, request
 

 # set FLASK_APP=skyfield_ISS.py && set FLASK_ENV=development
 # 

##===============================================##
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False # might cause issues but cant figure out how else to stop reordering json
##===============================================##

# root page; could update to return a json with url inputs and examples
@app.route('/')
def welcome():  
        return 'Welcome to the satellite tracking page.'

# current position of a specified satellite
@app.route('/satellite/<sat>')
def sat_data(sat):

    stations_url = 'http://celestrak.com/NORAD/elements/stations.txt'
    satellites = load.tle(stations_url, reload=True)
    satellite = satellites[str(sat)]

    ts = load.timescale()
    t = ts.now()

    geocentric = satellite.at(t)

    ground_station = Topos('30.287475 N', '97.735739 W')
    difference = satellite - ground_station

    topocentric = difference.at(t)
    el, az, distance = topocentric.altaz()

    if el.degrees > 0:
            visibility = True
    else:
            visibility = False

    sat_dict = {'Satellite' : sat,
                    'Current Azimuth:' : str(az.degrees),
                    'Current Elevation:': str(el.degrees),
                    'Current Time (UTC):' : str(t.utc_jpl()),
                    'Visible from Austin' : visibility}
    return jsonify(sat_dict)

# method to retrieve the state of a satellite at some time: takes in mm-dd-yyyy hh:mm:ss format as key value
@app.route('/satellite/<sat>/futurestate')
def state_at_time(sat):  # not sure what format time should be read in as: assuming mm-dd-yyyy hh:mm:ss
                               # and will calculate all passes for that day
    state_time = request.args.get('state_time')
    state_dtime = datetime.strptime(state_time, "%m-%d-%Y %H:%M:%S")  #might want to use  date time ISO format
    state_dtime = state_dtime.replace(tzinfo=utc)

    stations_url = 'http://celestrak.com/NORAD/elements/stations.txt'
    satellites = load.tle(stations_url, reload=True)
    satellite = satellites[str(sat)]
    
    
    ts = load.timescale()
    t = ts.utc(state_dtime)

    # geocentric = satellite.at(t)

    ground_station = Topos('30.287475 N', '97.735739 W')
    difference = satellite - ground_station

    topocentric = difference.at(t)
    el, az, distance = topocentric.altaz()

    if el.degrees > 0:
        visibility = True
    else:
        visibility = False

    sat_dict = {'Satellite' : sat,
                'Current Azimuth:' : str(az.degrees),
                'Current Elevation:': str(el.degrees),
                'Current Time (UTC):' : str(t.utc_jpl()),
                'Visible from Austin' : visibility}
    
    return jsonify(sat_dict)

# method to retrieve the number of passes between now and a specified future time: takes in mm-dd-yyyy hh:mm:ss format as key value
@app.route('/satellite/<sat>/futurepass')
def future_passes(sat):
    check_till = request.args.get('check_till')
    check_till = datetime.strptime(check_till, "%m-%d-%Y %H:%M:%S") #might want to use  date time ISO format
    check_till = check_till.replace(tzinfo=utc)

    check_till_sec = timegm(check_till.timetuple())
    now_time_sec = time.time()

    stations_url = 'http://celestrak.com/NORAD/elements/stations.txt'
    satellites = load.tle(stations_url, reload=True)
    satellite = satellites[str(sat)]
    
    ts = load.timescale()
    t = ts.utc(check_till)
    t_now = ts.now()

    ground_station = Topos('30.287475 N', '97.735739 W')
    difference = satellite - ground_station

    sat_data = {}
    pass_num = 0

    for times in range(floor(now_time_sec), floor(check_till_sec), 30):
        check_till_ts = datetime.utcfromtimestamp(times)
        check_till_ts = check_till_ts.replace(tzinfo=utc)

        now_time_ts = datetime.utcfromtimestamp(now_time_sec)
        now_time_ts = now_time_ts.replace(tzinfo=utc)

        t = ts.utc(check_till_ts)

        topocentric = difference.at(t)
        el, az, distance = topocentric.altaz()

        if el.degrees > 0:  # right now it calculates every 30 seconds which is why there are so many 
                pass_num += 1
                visibility = True
                sat_data.update({'Pass {}'.format(pass_num) :
                        {'Satellite' : sat,
                        'Pass Initial Azimuth:' : str(az.degrees),
                        'Pass Initial Elevation:': str(el.degrees),
                        'Pass Initial Time (UTC):' : str(t.utc_jpl()),
                        'Visible from Austin' : visibility}})
        else:
                visibility = False
    
    return jsonify(sat_data)
        

# To do
# 