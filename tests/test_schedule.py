#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''Unit tests for civilite.schedule'''
# Builtins
import calendar
import json
import os
import re
import time
from datetime import date, datetime, timedelta

# 3rd party
import pytz
from bs4 import BeautifulSoup
from dateutil.parser import parse
from requests import request

# Our stuff
from civilite import schedule

RE_NUMERIC = re.compile(r'\d+')


class TestSchedule:
    '''Test suite for everything related to scheduling in civilite.'''

    def test_sunsets(self):
        '''Verify that the civil sunsets for the current year match
            an independent source within a few minutes.'''
        test_year = datetime.now().year
        local_tz = pytz.timezone('US/Eastern')
        # minimum number of seconds between HTTP requests
        min_request_interval = 1.0
        last_request_time = datetime.now() - timedelta(minutes=min_request_interval*2.0)

        cache_filename = 'astro_cache.json'
        cache_needs_update = False
        astro_cache = {}
        if os.path.exists(cache_filename):
            astro_cache = json.load(open(cache_filename, 'r'))

        for test_month in range(1, 13):
            if date(test_year, test_month, 1).isoformat() not in astro_cache:
                cache_needs_update = True
                if (datetime.now() - last_request_time).total_seconds() < min_request_interval:
                    # don't bang the poor server to death
                    time.sleep(min_request_interval)
                url = f'https://www.timeanddate.com/sun/usa/rochester?month={test_month}&year={test_year}'
                print(f'{datetime.now()} : Sending a GET request to {url}')
                response = request('GET', url)
                soup = BeautifulSoup(response.content, features='html.parser')
                header = soup('tr', {'class': 'bg-wt'})[0]

                # The values we want are in the "Sunrise" and "Sunset" columns.
                # These are <td> tag indexes 0 and 1. The day of month is in a <th> tag.
                # T&D.com defines sunrise as the end of civil twilight in the morning, and
                # sunset as the beginning of civil twilight in the evening.
                # The columns labeled Start and End under the "Civil Twilight" column define the duration
                # of the whole day including the absolute start and absolute end of twilight phases for the day.
                day_tags = soup('tr', {'data-day': RE_NUMERIC})
                num_days = calendar.monthlen(test_year, test_month)
                assert num_days == len(day_tags), \
                    f'Unexpected number of parsed days in month {test_month}/{test_year}'
                for day_tag in day_tags:
                    test_day = int(day_tag('th')[0].string)
                    test_datetime = datetime(test_year, test_month, test_day)
                    # first two <td> tags are the sunrise & sunset cells.
                    # grab just the time expression via .contents, forget the rise/set symbol and azimuth in string
                    sun_times = [dt.contents[0] for dt in day_tag('td')[:2]]
                    # parse each time, dump to an ISO-formatted string for JSON storage
                    sunrise, sunset = [local_tz.localize(parse(t, default=test_datetime)).isoformat()
                                       for t in sun_times]
                    # cache the data
                    astro_cache[test_datetime.date().isoformat()] = sunrise, sunset
        if cache_needs_update:
            json.dump(astro_cache, open(cache_filename, 'w'))

        curr_schedule = schedule.getCurrentSchedule()
        curr_events = curr_schedule.createEvents(test_year)
        for evt_date, (sunset_time, *etc) in curr_events.items():
            expected_sunset = parse(astro_cache[evt_date.isoformat()][1])
            abs_sunset_diff = abs(sunset_time - expected_sunset)
            # print(f'  expected sunset: {expected_sunset}')
            # print(f'calculated sunset: {sunset_time}')
            # print(f'             diff: {abs_sunset_diff}')
            assert abs_sunset_diff.total_seconds() < 120.0, f'Unexpected sunset time on {evt_date}'
