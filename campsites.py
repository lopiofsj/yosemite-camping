#!/usr/bin/env python
import argparse
import copy
import requests

import urllib
from urlparse import parse_qs
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Hardcoded list of campgrounds I'm willing to sleep at
PARKS = {
    '70925': 'UPPER PINES',
    '70926': 'TUOLOMNE MEADOWS',
    '70927': 'NORTH PINES',
    '70928': 'LOWER PINES',
    '70929': 'HODGDON MEADOW',
    '70930': 'CRANE FLAT',
    '73635': 'STANISLAUS',
}

# Sets the search location to yosemite
LOCATION_PAYLOAD = {
    'currentMaximumWindow': '12',
    'locationCriteria': 'yosemite',
    'interest': '',
    'locationPosition': '',
    'selectedLocationCriteria': '',
    'resetAllFilters':    'false',
    'filtersFormSubmitted': 'false',
    'glocIndex':    '0',
    'googleLocations':  'Yosemite National Park, Yosemite Village, CA 95389, USA|-119.53832940000001|37.8651011||LOCALITY'  # noqa: E501
}

# Sets the search type to camping
CAMPING_PAYLOAD = {
    'resetAllFilters':  'false',
    'filtersFormSubmitted': 'true',
    'sortBy':   'RELEVANCE',
    'category': 'camping',
    'selectedState':    '',
    'selectedActivity': '',
    'selectedAgency':   '',
    'interest': 'camping',
    'usingCampingForm': 'true'
}

# Runs the actual search
PAYLOAD = {
    'resetAllFilters':   'false',
    'filtersFormSubmitted': 'true',
    'sortBy':   'RELEVANCE',
    'category': 'camping',
    'availability': 'all',
    'interest': 'camping',
    'usingCampingForm': 'false'
}


BASE_URL = "https://www.recreation.gov"
UNIF_SEARCH = "/unifSearch.do"
UNIF_RESULTS = "/unifSearchResults.do"


def findCampSites(args):
    payload = generatePayload(args['start_date'], args['end_date'])

    content_raw = sendRequest(payload)
    html = BeautifulSoup(content_raw, 'html.parser')
    sites = getSiteList(html)
    return sites


def getNextDay(date):
    date_object = datetime.strptime(date, "%Y-%m-%d")
    next_day = date_object + timedelta(days=1)
    return datetime.strftime(next_day, "%Y-%m-%d")


def formatDate(date):
    date_object = datetime.strptime(date, "%Y-%m-%d")
    date_formatted = datetime.strftime(date_object, "%a %b %d %Y")
    return date_formatted


def generatePayload(start, end):
    payload = copy.copy(PAYLOAD)
    payload['arrivalDate'] = formatDate(start)
    payload['departureDate'] = formatDate(end)
    return payload


def getSiteList(html):
    sites = html.findAll('div', {"class": "check_avail_panel"})
    results = []
    for site in sites:
        if site.find('a', {'class': 'book_now'}):
            get_url = site.find('a', {'class': 'book_now'})['href']
            # Strip down to get query parameters
            if get_url.find("?") >= 0:
                get_query = get_url[get_url.find("?") + 1:]
            else:
                get_query = get_url
            if get_query:
                get_params = parse_qs(get_query)
                siteId = get_params['parkId']
                if siteId and siteId[0] in PARKS:
                    msg = "%s, Booking Url: %s"
                    found_url = BASE_URL + get_url
                    results.append(msg % (PARKS[siteId[0]], found_url))
    return results


def sendRequest(payload):
    with requests.Session() as s:
        # Sets session cookie
        s.get(BASE_URL + UNIF_RESULTS, verify=True)
        # Sets location to yosemite
        s.post(BASE_URL + UNIF_SEARCH, LOCATION_PAYLOAD, verify=True)
        # Sets search type to camping
        s.post(BASE_URL + UNIF_SEARCH, CAMPING_PAYLOAD, verify=True)

        # Runs search on specified dates
        resp = s.post(BASE_URL + UNIF_SEARCH, payload, verify=True)
        if (resp.status_code != 200):
            msg = "ERROR, %d code received from %s"
            failed_url = BASE_URL + UNIF_SEARCH
            raise Exception("failedRequest", msg.format(resp.status_code,
                                                        failed_url))
        else:
            return resp.text


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start_date",
                        required=True,
                        type=str,
                        help="Start date [YYYY-MM-DD]")
    parser.add_argument("--end_date",
                        type=str,
                        help="End date [YYYY-MM-DD]")

    args = parser.parse_args()
    arg_dict = vars(args)
    if 'end_date' not in arg_dict or not arg_dict['end_date']:
        arg_dict['end_date'] = getNextDay(arg_dict['start_date'])

    sites = findCampSites(arg_dict)
    if sites:
        for site in sites:
            print site + \
                "&arrivalDate={}&departureDate={}" \
                .format(
                        urllib.quote_plus(formatDate(arg_dict['start_date'])),
                        urllib.quote_plus(formatDate(arg_dict['end_date'])))
    else:
        print('Nothing Found')
