import datetime
import urlparse

import requests
import xmltodict

import constants


class BartApi():
    """Bay Area Rapid Transit API Implementation"""

    BART_URI = 'http://api.bart.gov/api/'
    BART_ENDPOINTS = ['bsa', 'etd', 'route', 'sched', 'stn']

    def __init__(self, api_key):
        self.api_key = api_key

    # Utilities

    def _get_api_endpoint(self, endpoint):
        """Get the api endpoint"""
        if endpoint in self.BART_ENDPOINTS:
            return urlparse.urljoin(self.BART_URI, '{}.aspx'.format(endpoint))
        raise Exception("Endpoint '{}' does not exist".format(endpoint))

    def call_api(self, endpoint, cmd, **kwargs):
        """Call the API with the cmd, key and any kwargs"""
        payload = {'cmd': cmd, 'key': self.api_key}
        payload.update(**kwargs)
        uri = self._get_api_endpoint(endpoint)
        resp = requests.get(uri, params=payload)
        if resp.status_code != 200:
            resp.raise_for_status()
        out = xmltodict.parse(resp.content)['root']
        out.pop('uri')
        if out['message']:
            error = out['message'].get('error', None)
            if error:
                print error
        return out

    # Param Checking

    def check_station(self, orig):
        """Raise Exception if station not valid"""
        if orig.lower() not in constants.stations.keys() + ['all']:
            raise Exception("Station '{}' not recognized".format(orig))

    def check_platform(self, platform):
        """Raise Exception if platform not valid"""
        if platform not in range(1, 5):
            raise Exception("Platform '{}' not recognized".format(platform))

    def check_direction(self, direction):
        """Raise Exception if direction not valid"""
        if direction not in 'ns':
            raise Exception("Direction '{}' not recognized".format(direction))

    def check_route(self, route):
        """Raise Exception if route not valid"""
        if route not in constants.routes + ['all', 'ALL']:
            raise Exception("Route '{}' not recognized".format(route))

    def check_time(self, time):
        """
        Raise Exception if time not valid

        Time can be 'now' or formatted as h:mm+am/pm
        """
        if time not in ['today', 'now']:
            try:
                datetime.datetime.strptime(time, '%H:%M+%p')
            except:
                raise Exception("Time '{}' not recognized".format(time))

    def check_date(self, date):
        """
        Raise Exception if date not valid

        Date can be 'today', 'now', or formatted as mm/dd/yyyy
        """
        if date not in ['today', 'now']:
            try:
                datetime.datetime.strptime(date, '%m/%d/%Y')
            except:
                raise Exception("Date '{}' not recognized".format(date))

    def check_trips(self, num_trips):
        """
        Raise Exception if number of trips exceeds 4
        """
        if num_trips not in range(0, 5):
            msg = "Number of given trips, {}, not valid".format(num_trips)
            raise Exception(msg)

    def check_legend(self, legend):
        """Raise Exception if legend value invalid"""
        if legend not in [0, 1]:
            raise Exception("Legend value '{}' invalid".format(legend))

    def check_load(self, train):
        """
        Raise Exception if load parameter invalid

        Station, Route, and Train ID. The
        format for this parameter is a four letter station
        code, a two digit route (left padded with 0 if needed)
        and a two digit train id. The train id (trainIdx)
        information is included in the <leg> element of the
        results of a arrive/depart request. (Optional)
        """
        station = train[:4]
        route = train[4:6]
        train_id = train[6:]
        if station not in constants.stations.keys():
            raise Exception("Station '{}' not recognized".format(station))
        try:
            int(route)
        except Exception:
            raise Exception("Route '{}' not recognized".format(route))
        try:
            int(train_id)
        except Exception:
            raise Exception("Train ID '{}' not recognized".format(train_id))

    def check_schedule_type(self, st):
        """
        Raise an Exception if station type invalid.

        Schedule type for this request. Schedule type is a single
        character representing Weekday (W), Saturday (S) or
        Sunday/Holiday (H). (Required)
        """
        if st.lower() not in 'wsh':
            raise Exception("Station type '{}' not recognized".format(st))

    # Common API Calls

    def get_api_commands(self, endpoint):
        """Provides a summary of the commands available through the BSA API"""
        if endpoint not in self.BART_ENDPOINTS:
            raise Exception("Endpoint '{}' does not exist".format(endpoint))
        out = self.call_api(endpoint, 'help')['message']['help']
        return out.split(': ')[1].split(', ')

    def get_api_version(self, endpoint='bsa'):
        """Provides the current version number of the BART API"""
        return self.call_api(endpoint, 'ver')

    # Advisory Information API

    def get_current_advisory(self, orig='all'):
        """
        Requests current bsa information

        orig=<stn>  Only get messages for specified station. Defaults to "all".
                    (Optional) [Note: currently only "orig=all" or leaving the
                    orig parameter off are supported, the BART system does not
                    currently provide station specific BSA messages.]

        Notes:

        Currently all BSA messages have a station code of "BART" signifying
        that they are system-wide. If future messages are tagged for specific
        stations, and a station is specified in the orig parameter, information
        will be provided for the specified station as well as any system-wide
        tagged messages. To get all messages, regardless of tags, specify
        "orig=all".

        The "type" element will either be DELAY or EMERGENCY. The "sms_text"
        element is a contracted version of the "description" element for use
        with text messaging. This element might be longer than allowed in a
        single text message, so it might need to be broken up into several
        messages.
        """
        self.check_station(orig)
        return self.call_api('bsa', 'bsa', orig=orig)['bsa']

    def get_number_of_trains(self):
        """Request the number of trains currently active in the system"""
        return self.call_api('bsa', 'count')['traincount']

    def get_elevator_status(self):
        """Requests current elevator status information"""
        return self.call_api('bsa', 'elev')['bsa']

    # Real-Time Information API

    def get_estimated_departure(self, orig='all', plat=None, dir=None):
        """
        Requests estimated departure time for specified station

        orig=<station>  Specifies the station. Stations are referenced by
                        their abbreviations. You can also use 'ALL' to get all
                        of the current ETD's. (Required)
        plat=<platform> This will limit results to a specific platform. Valid
                        platforms depend on the station, but can range from
                        1-4. (Optional)
        dir=<dir>       This will limit results to a specific direction. Valid
                        directions are 'n' for Northbound and 's' for
                        Southbound. (Optional)

        Notes:

        The optional parameters 'plat' and 'dir' should not be used together.
        If they are, then the 'dir' parameter will be ignored and just the
        platform parameter will be used.

        If 'ALL' is used for the orig station, then 'plat' and 'dir' cannot
        be used.
        """
        self.check_station(orig)
        if orig == 'all':
            return self.call_api('etd', 'etd', orig=orig)
        elif plat:
            self.check_platform(plat)
            return self.call_api('etd', 'etd', orig=orig, plat=plat)
        elif dir:
            self.check_direction(dir)
            return self.call_api('etd', 'etd', orig=orig, dir=dir)

    # Route Information API

    def get_route_information(self, route='all', sched=None, date='today'):
        """
        Requests detailed information regarding a specific route

        route=<route_num>   Specifies the specific route information to return
                            In addition to route number (i.e. 1, 2, ... 12)
                            'all' can be specified to get the configuration
                            information for all routes. (Required)
        sched=<sched_num>   Specifies a specific schedule to use. Defaults to
                            current schedule. (Optional)
        date=<mm/dd/yyyy>   Specifies a specific date to use. This will
                            determine the appropriate schedule for that date,
                            and give back information about the routes for
                            that schedule. Date can also be specified as
                            "today" or "now". (Optional)

        Notes:

        Route information is sometimes updated with schedule changes as routes
        are reconfigured. This may affect the name and abbreviation of the
        route, as well as the number of stations.

        The optional "date" and "sched" parameters should not be used together.
        If they are, the date will be ignored, and the sched parameter will be
        used.
        """
        self.check_route(route)
        self.check_date(date)

        if not sched:
            return self.call_api('route', 'routeinfo', route=route, date=date)
        else:
            return self.call_api('route', 'routeinfo', route=route,
                                 sched=sched, date=date)

    def get_route_current_information(self, sched=None, date='today'):
        """
        Requests detailed information current routes

        sched=<sched_num>   Specifies a specific schedule to use. Defaults to
                            current schedule. (Optional)
        date=<mm/dd/yyyy>   Specifies a specific date to use. This will
                            determine the appropriate schedule for that date,
                            and give back information about the routes for
                            that schedule. Date can also be specified as
                            "today" or "now". (Optional)

        Notes:

        Route information is sometimes updated with schedule changes as routes
        are reconfigured. This may affect the name and abbreviation of the
        route, as well as the number of stations.

        The optional "date" and "sched" parameters should not be used together.
        If they are, the date will be ignored, and the sched parameter will be
        used.
        """
        self.check_date(date)

        if not sched:
            return self.call_api('route', 'routes', date=date)
        else:
            return self.call_api('route', 'routes', sched=sched, date=date)

    # Schedule Information API

    def get_schedule_by_arrival(self, orig, dest,
                                time='now', date='today',
                                trips_before=2, trips_after=2,
                                legend=0):
        """
        Requests a trip plan based on arriving by the specified time.

        orig=<station>  Specifies the origination station. Stations should be
                        specified using the four character abbreviations.
                        (Required)
        dest=<station>  Specifies the destination station. Stations should be
                        specified using the four character abbreviations.
                        (Required)
        time=h:mm+am/pm Specifies the arrival time for the trip. Using
                        "time=now" is also valid and will return the specified
                        trips based on the current time. If not specified,
                        defaults to the current time. (Optional)
        date=<mm/dd/yyyy>   Specifies a specific date to use for calculating
                            the trip. This will determine the appropriate
                            schedule for that date, and give back information
                            about the lines for that schedule. Date can also be
                            specified as "today" or "now". The default is the
                            current date. (Optional)
        b=<number>  This allows specifying how many trips before the specified
                    time should be returned. This paramter defaults to 2, and
                    can be set between 0 and 4. (Optional)
        a=<number>  This allows specifying how many trips after the specified
                    time should be returned. This paramter defaults to 2, and
                    can be set between 0 and 4. (Optional)
        l=<number>  Specifies whether the legend information should be
                    included. By default it is 0 (not shown), but can be turned
                    on by setting it to 1. (Optional)

        Notes:

        Trips can contain from 1 to 3 legs, depending on the number of
        transfers that are required. Special schedule messages will only be
        displayed if the trip date, time, and orig or dest stations match a
        special schedule notice.
        """
        self.check_station(orig)
        self.check_station(dest)
        self.check_time(time)
        self.check_date(date)
        self.check_trips(trips_before)
        self.check_trips(trips_after)
        self.check_legend(legend)
        return self.call_api('sched', 'arrive',
                             orig=orig, dest=dest,
                             time=time, date=date,
                             b=trips_before, a=trips_after,
                             l=legend)

    def get_schedule_by_departure(self, orig, dest,
                                  time='now', date='today',
                                  trips_before=2, trips_after=2,
                                  legend=0):
        """
        Requests a trip plan based on departing by the specified time.

        orig=<station>  Specifies the origination station. Stations should be
                        specified using the four character abbreviations.
                        (Required)
        dest=<station>  Specifies the destination station. Stations should be
                        specified using the four character abbreviations.
                        (Required)
        time=h:mm+am/pm Specifies the arrival time for the trip. Using
                        "time=now" is also valid and will return the specified
                        trips based on the current time. If not specified,
                        defaults to the current time. (Optional)
        date=<mm/dd/yyyy>   Specifies a specific date to use for calculating
                            the trip. This will determine the appropriate
                            schedule for that date, and give back information
                            about the lines for that schedule. Date can also be
                            specified as "today" or "now". The default is the
                            current date. (Optional)
        b=<number>  This allows specifying how many trips before the specified
                    time should be returned. This paramter defaults to 2, and
                    can be set between 0 and 4. (Optional)
        a=<number>  This allows specifying how many trips after the specified
                    time should be returned. This paramter defaults to 2, and
                    can be set between 0 and 4. (Optional)
        l=<number>  Specifies whether the legend information should be
                    included. By default it is 0 (not shown), but can be turned
                    on by setting it to 1. (Optional)

        Notes:

        Trips can contain from 1 to 3 legs, depending on the number of
        transfers that are required. Special schedule messages will only be
        displayed if the trip date, time, and orig or dest stations match a
        special schedule notice.
        """
        self.check_station(orig)
        self.check_station(dest)
        self.check_time(time)
        self.check_date(date)
        self.check_trips(trips_before)
        self.check_trips(trips_after)
        self.check_legend(legend)
        return self.call_api('sched', 'depart',
                             orig=orig, dest=dest,
                             time=time, date=date,
                             b=trips_before, a=trips_after,
                             l=legend)

    def get_schedule_fare(self, orig, dest, date='today', sched=None):
        """
        Requests fare information for a trip between two stations.

        orig=<station>  Specifies the origination station. Stations should be
                        specified using the four character abbreviations.
                        (Required)
        dest=<station>  Specifies the destination station. Stations should be
                        specified using the four character abbreviations.
                        (Required)
        date=<mm/dd/yyyy>   Specifies a specific date to use for calculating
                            the fare. If not specified, the current date will
                            be used. Also the terms "now" or "today" may be
                            used instead of "mm/dd/yyyy". (Optional)
        sched=<number>  Specifies a specific schedule to use. (Optional)

        Notes:

        The optional "date" and "sched" parameters should not be used together.
        If they are, the date will be ignored, and the sched parameter will be
        used.
        """
        self.check_station(orig)
        self.check_station(dest)
        self.check_date(date)
        if sched:
            return self.call_api('sched', 'fare', orig=orig, dest=dest,
                                 date=date, sched=sched)
        else:
            return self.call_api('sched', 'fare', orig=orig, dest=dest,
                                 date=date)

    def get_schedule_for_holiday(self):
        """
        Requests information on the upcoming BART holidays, and what type of
        schedule will be run on those days.

        Notes:

        On BART Holidays, the trains may run on a different schedule from
        normal. This typically will mean that a Sunday/Holiday schedule will be
        used, however, sometimes a Saturday schedule is used. The Schedule
        Information API will automatically use the appropriate schedule for any
        trip that coincides with a BART holiday. In addition, a message will be
        appended to the trip results stating that a holiday schedule was used.
        """
        return self.call_api('sched', 'holiday')

    def get_schedule_load_factor(self, ld1, ld2=None, ld3=None, st='W'):
        """
        Requests estimated load factor for specified train(s).

        ld1=<ssssrrtt>  First train to get the estimated load factor for. The
                        format for this parameter is a four letter station
                        code, a two digit route (left padded with 0 if needed)
                        and a two digit train id. The train id (trainIdx)
                        information is included in the <leg> element of the
                        results of a arrive/depart request. (Required)
        ld2=<ssssrrtt>  Second train to get the estimated load factor for. The
                        format for this parameter is a four letter station
                        code, a two digit route (left padded with 0 if needed)
                        and a two digit train id. The train id (trainIdx)
                        information is included in the <leg> element of the
                        results of a arrive/depart request. (Optional)
        ld3=<ssssrrtt>  Third train to get the estimated load factor for. The
                        format for this parameter is a four letter station
                        code, a two digit route (left padded with 0 if needed)
                        and a two digit train id. The train id (trainIdx)
                        information is included in the <leg> element of the
                        results of a arrive/depart request. (Optional)
        st=<W|S|H>  Schedule type for this request. Schedule type is a single
                    character representing Weekday (W), Saturday (S) or
                    Sunday/Holiday (H). (Required)

        Notes:

        The load factor command takes from 1 to 3 ld parameters, each
        representing the start of a trip leg so that for any given trip you
        can get information for the entire trip in a single call. Currently
        there are only load factor estimates for Weekday schedules.

        As an example of how this would be used, say you want to find the load
        information for a trip between Ashby and Colma. That trip has either
        1 leg (Millbrae Line) or 2 legs (Fremont --> SFIA lines). To get the
        load factor for each of those trips, you might use the following
        calls:

        http://api.bart.gov/api/sched.aspx?cmd=load&ld1=ASHB0746&st=w&key=MW9S-E7SL-26DU-VV8V

        to get the Millbrae trip information and

        http://api.bart.gov/api/sched.aspx?cmd=load&ld1=ASHB0446&ld2=MCAR0159&st=w&key=MW9S-E7SL-26DU-VV8V

        for the Fremont to SFIA trip, which has a transfer at MCAR.

        Currently the official BART website shows the estimated load factor for
        the train at the origin station and at any transfer stations.

        The results will display as many leg elements as there were ld
        parameters specified on the API call. If a load factor is not found for
        a given schedule type or ld specified, the load attribute will be "-1",
        otherwise a load of 1-3 will be displayed.
        """
        self.check_load(ld1)
        if ld2:
            self.check_load(ld2)
        if ld3:
            self.check_load(ld3)
        self.check_schedule_type(st)

        if all(ld1, ld2, ld3):
            return self.call_api('sched', 'load',
                                 ld1=ld1, ld2=ld2, ld3=ld3, st=st)
        elif all(ld1, ld2):
            return self.call_api('sched', 'load',
                                 ld1=ld1, ld2=ld2, st=st)
        else:
            return self.call_api('sched', 'load',
                                 ld1=ld1, st=st)

    def get_schedule_by_route(self):
        """Requests a full schedule for the specified route."""
        return self.call_api('sched', 'routesched')

    def get_schedule(self):
        """Requests information about the currently available schedules."""
        return self.call_api('sched', 'scheds')

    def get_schedule_special(self):
        """
        Requests information about all special schedule notices in effect.
        """
        return self.call_api('sched', 'special')

    def get_schedule_station(self):
        """
        Requests an entire daily schedule for the particular station specified.
        """
        return self.call_api('sched', 'stnsched')

    # Station Information API

    def get_station_access(self, orig='all', legend=0):
        """
        Requests detailed information how to access the specified station
        as well as information about the neighborhood around the station.
        """
        self.check_station(orig)
        self.check_legend(legend)

        out = self.call_api('stn', 'stnaccess', orig=orig, l=legend)
        stations = {'stations': out['stations']}
        if legend == 1:
            stations['legend'] = out['message']['legend']
        return stations

    def get_station_info(self, orig):
        """Provides a detailed information about the specified station."""
        self.check_station(orig)
        return self.call_api('stn', 'stninfo', orig=orig)['stations']

    def get_stations(self):
        """Provides a list of all available stations."""
        return self.call_api('stn', 'stns')['stations']
