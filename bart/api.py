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

    def check_route(self, route):
        """Raise Exception if route not valid"""
        if route not in constants.routes + ['all', 'ALL']:
            raise Exception("Route '{}' not recognized".format(route))

    def check_date(self, date):
        """Raise Exception if date not valid"""
        if date not in ['today', 'now']:
            try:
                datetime.datetime.strptime(date, '%M/%D/%Y')
            except:
                raise Exception("Date '{}' not recognized".format(date))

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

    def get_bsa_current_advisory(self, orig='all'):
        """Requests current bsa information"""
        self.check_station(orig)
        return self.call_api('bsa', 'bsa', orig=orig)['bsa']

    def get_bsa_number_of_trains(self):
        """Request the number of trains currently active in the system"""
        return self.call_api('bsa', 'count')['traincount']

    def get_bsa_elevator_status(self):
        """Requests current elevator status information"""
        return self.call_api('bsa', 'elev')['bsa']

    # Real-Time Information API

    def get_etd_estimated_departure(self, orig='all', plat=None, dir=None):
        """Requests estimated departure time for specified station"""
        self.check_station(orig)
        if orig == 'all':
            return self.call_api('etd', 'etd', orig=orig)
        elif plat:
            return self.call_api('etd', 'etd', orig=orig, plat=plat)
        elif dir:
            if dir not in 'nsew':
                raise Exception("Direction '{}' not recognized".format(dir))
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

    # Station Information API

    def get_stn_access(self, orig='all', legend=0):
        """
        Requests detailed information how to access the specified station
        as well as information about the neighborhood around the station.
        """
        self.check_station(orig)
        out = self.call_api('stn', 'stnaccess', orig=orig, l=legend)
        stations = {'stations': out['stations']}
        if legend == 1:
            stations['legend'] = out['message']['legend']
        return stations

    def get_stn_info(self, orig):
        """Provides a detailed information about the specified station."""
        self.check_station(orig)
        return self.call_api('stn', 'stninfo', orig=orig)['stations']

    def get_stns(self):
        """Provides a list of all available stations."""
        return self.call_api('stn', 'stns')['stations']
