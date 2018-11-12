import json
from datetime import datetime
import time
from calendar import timegm
from math import floor, degrees

from skyfield.api import Topos, load, utc
from skyfield.units import Angle

from flask import Flask, jsonify, request

# sets up a cache to pull the future pass data from to get the more detailed pass info
from functools import wraps
from flask import request
from werkzeug.contrib.cache import SimpleCache

import sat_data_strut
 
 # set FLASK_APP=skyfield_ISS.py && set FLASK_ENV=development
 # 

##===============================================##
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False # might cause issues but cant figure out how else to stop reordering json
##===============================================##




cache = SimpleCache()
def cached(timeout=30 * 60, key='view/%s'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            cache_key = 'passes'
            rv = cache.get(cache_key)
            rv = f(*args, **kwargs)
            cache.set(cache_key, rv, timeout=timeout)
            if rv is not None:
                return rv
            return rv
        return decorated_function
    return decorator

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
@cached()
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
                                        find_pass_start_time = datetime.utcfromtimestamp(find_pass_start_sec)
                                        find_pass_start_time = find_pass_start_time.replace(tzinfo=utc)

                                        t_check = ts.utc(find_pass_start_time)

                                        topocentric = difference.at(t_check)
                                        el_check, az_check, distance = topocentric.altaz()

                                        pass_num += 1
                                        pass_time.append(t_check.utc_jpl())
                                        visibility = True
                                        state.append({'azimuth' : str(az_check.degrees), 'elevation' : str(el_check.degrees)}) # pass start az el
                                        
                                        # sat_data.update({'Pass {}'.format(pass_num) :
                                        # {'Satellite' : sat,
                                        # 'Pass Initial Azimuth:' : str(az.degrees),
                                        # 'Pass Initial Elevation:': str(el.degrees),
                                        # 'Pass Initial Time (UTC):' : str(pass_time.utc_jpl()),
                                        # 'Visible from Austin' : visibility}})
                                        break
                
        else:
                visibility = False

    sat_data.update(
                   {'spacecraft ' : sat,
                    'times' : pass_time,
                    'states' : state})
    
    return jsonify(sat_data)

@app.route('/satellite/<sat>/passinfo')
def info(sat):
    pass_number = request.args.get('passnum')
    time_interval = float(request.args.get('interval'))

    sat_data = cache.get('passes').get_json()
    initial_t = sat_data['times'][int(pass_number)-1]
    

    initial_t_dt = datetime.strptime(initial_t, "A.D. %Y-%b-%d %H:%M:%S.%f UT") 
    initial_t_dt = initial_t_dt.replace(tzinfo=utc)

    initial_t_sec = timegm(initial_t_dt.timetuple())


    stations_url = 'http://celestrak.com/NORAD/elements/stations.txt'
    satellites = load.tle(stations_url, reload=True)
    satellite = satellites[str(sat)]
    
    ts = load.timescale()

    ground_station = Topos('30.287475 N', '97.735739 W')
    difference = satellite - ground_station
    
    t = ts.utc(initial_t_dt)

    topocentric = difference.at(t)
    el, az_check, distance = topocentric.altaz()
    
    elapse_time = 0
    pass_time = []
    state = []
    sat_data1 = {}
    while el.degrees > 0 and elapse_time < (60*60*2):
         # 10 second interval between states
        if elapse_time == 0:
                find_pass_end = initial_t_sec 
        else:
                find_pass_end += time_interval
        find_pass_end_time = datetime.utcfromtimestamp(find_pass_end)
        find_pass_end_time = find_pass_end_time.replace(tzinfo=utc)

        t_check = ts.utc(find_pass_end_time)

        topocentric = difference.at(t_check)
        el, az, distance = topocentric.altaz()
        if el.degrees < 0:
                break
                
        pass_time.append(t_check.utc_jpl())
        state.append({'azimuth' : str(az.degrees), 'elevation' : str(el.degrees)})
        elapse_time += time_interval

#     print(state)
#     print(pass_time)
    sat_data1.update({'spacecraft ' : sat,
                     'times' : pass_time,
                     'states' : state})
 
 
    return jsonify(sat_data1)