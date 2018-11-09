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

    sat_data = {'spacecraft ' : sat,
                    'times' : t.utc_jpl(),
                    'states' : {'azimuth' : str(az.degrees), 'elevation' : str(el.degrees)}}
    return jsonify(sat_data)

# method to retrieve the state of a satellite at some time: takes in mm-dd-yyyy hh:mm:ss format as key value
@app.route('/satellite/<sat>/futurestate')
def state_at_time(sat):  # not sure what format time should be read in as: assuming mm-dd-yyyy hh:mm:ss
                               # and will calculate all passes for that day
    state_time = request.args.get('state_time')
    state_dtime = datetime.strptime(state_time, "%Y-%m-%dT%H:%M:%SZ")  #might want to use  date time ISO format
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

    sat_data = {'spacecraft ' : sat,
                    'times' : t.utc_jpl(),
                    'states' : {'azimuth' : str(az.degrees), 'elevation' : str(el.degrees)}}
    

#     sat_dict = {'Satellite' : sat,
#                 'Current Azimuth:' : str(az.degrees),
#                 'Current Elevation:': str(el.degrees),
#                 'Current Time (UTC):' : str(t.utc_jpl()),
#                 'Visible from Austin' : visibility}
    
    return jsonify(sat_data)

# method to retrieve the number of passes between now and a specified future time: takes in mm-dd-yyyy hh:mm:ss format as key value
@app.route('/satellite/<sat>/futurepass')
def future_passes(sat):
    check_till = request.args.get('check_till')
    check_till = datetime.strptime(check_till, "%Y-%m-%dT%H:%M:%SZ") #might want to use  date time ISO format
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
    pass_time = []
    state = []
    az_json = []
    el_json = []

    for times in range(floor(now_time_sec), floor(check_till_sec), 60*5):
        check_till_ts = datetime.utcfromtimestamp(times)
        check_till_ts = check_till_ts.replace(tzinfo=utc)

        now_time_ts = datetime.utcfromtimestamp(now_time_sec)
        now_time_ts = now_time_ts.replace(tzinfo=utc)

        t = ts.utc(check_till_ts)

        topocentric = difference.at(t)
        el, az, distance = topocentric.altaz()

        if el.degrees > 0:
                find_pass_start_sec = times # time in seconds

                # find_pass_start_time = datetime.utcfromtimestamp(find_pass_start_sec)
                # find_pass_start_time = check_till_ts.replace(tzinfo=utc)

                for check_5_min_before in range(0,(60*5),1):
                        
                        find_pass_start_sec -= 1  # subtract 1 second till finds the first second in view
                        find_pass_start_time = datetime.utcfromtimestamp(find_pass_start_sec)
                        find_pass_start_time = find_pass_start_time.replace(tzinfo=utc)

                        t_check = ts.utc(find_pass_start_time)

                        topocentric = difference.at(t_check)
                        el_check, az_check, distance = topocentric.altaz()

                        if el_check.degrees > 0:
                                continue
                        else:
                                find_pass_start_sec += 1
                                if find_pass_start_time in pass_time == True: 
                                        break
                                else:
                                        pass_num += 1
                                        pass_time.append(t_check.utc_jpl())
                                        visibility = True
                                        # az_json.append(az_check)
                                        # el_json.append(el_check)
                                        state.append({'azimuth' : str(az_check.degrees), 'elevation' : str(el_check.degrees)})
                                        
                                        # sat_data.update({'Pass {}'.format(pass_num) :
                                        # {'Satellite' : sat,
                                        # 'Pass Initial Azimuth:' : str(az.degrees),
                                        # 'Pass Initial Elevation:': str(el.degrees),
                                        # 'Pass Initial Time (UTC):' : str(pass_time.utc_jpl()),
                                        # 'Visible from Austin' : visibility}})
                                        break
                
        else:
                visibility = False

    sat_data.update({'spacecraft ' : sat,
                    'times' : pass_time,
                    'states' : state})

    return jsonify(sat_data)
        

# To do
# 