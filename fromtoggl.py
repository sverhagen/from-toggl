#!/usr/bin/env python

import dateutil.parser
import logging
import os
import requests
import time as _time
from datetime import date, datetime, time, timedelta
from tzlocal import get_localzone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__package__)

today = date.today()
START_DATE = datetime.combine(today - timedelta(days=today.weekday()), time()).astimezone()
END_DATE = START_DATE + timedelta(days=7)

# ##### CONFIGURATION START #####
CLIENT_ID = 34710800
GAP = timedelta(minutes=10)
ROUNDING_ACCURACY = timedelta(minutes=5)
# START_DATE = date(2018, 1, 8)
# ##### CONFIGURATION END #####

ENVIRONMENT_VARIABLE_TOGGL_API_TOKEN = "TOGGL_API_TOKEN"
TIME_OFFSET = timedelta(hours=int(_time.altzone / 3600))


def get_api_token():
    if not ENVIRONMENT_VARIABLE_TOGGL_API_TOKEN in os.environ:
        raise EnvironmentError("missing {} environment variable, which should contain your Toggl API token".format(
            ENVIRONMENT_VARIABLE_TOGGL_API_TOKEN))

    return os.environ[ENVIRONMENT_VARIABLE_TOGGL_API_TOKEN]


auth = (get_api_token(), "api_token")

response = requests.get(
    "https://www.toggl.com/api/v8/clients/{}/projects".format(CLIENT_ID),
    auth=auth
)

data = response.json()
pids = [entry["id"] for entry in data]
logger.info("processing projects: {}".format(pids))
logger.info("start date: {}".format(START_DATE))
logger.info("end date: {}".format(END_DATE))

start_date_string = START_DATE.isoformat()
end_date_string = END_DATE.isoformat()

response = requests.get(
    "https://www.toggl.com/api/v8/time_entries?start_date={}&end_date={}".format(start_date_string, end_date_string),
    auth=auth
)

data = response.json()

results = []
previous_start = None
previous_stop = None


def ceil_dt(dt):
    min_dt = datetime.min - dt.replace(tzinfo=None)
    return dt + (min_dt % ROUNDING_ACCURACY)


def floor_dt(dt):
    min_dt = datetime.min - dt.replace(tzinfo=None)
    return dt - (ROUNDING_ACCURACY - min_dt % ROUNDING_ACCURACY) % ROUNDING_ACCURACY


def append_result():
    local_previous_start = previous_start

    if local_previous_start:
        start_time = (local_previous_start - TIME_OFFSET).time()
        stop_time = (previous_stop - TIME_OFFSET).time()

        if start_time > stop_time:
            results.append({
                "start": floor_dt(local_previous_start),
                "stop": ceil_dt(truncate_to_midnight(previous_stop)),
                "running": previous_currently_running
            })

            local_previous_start = truncate_to_midnight(previous_stop)

        results.append({
            "start": floor_dt(local_previous_start),
            "stop": ceil_dt(previous_stop),
            "running": previous_currently_running
        })


def truncate_to_midnight(previous_stop):
    truncated = datetime.combine(previous_stop.date(), time(hour=0))
    return truncated.astimezone(get_localzone())


for entry in data:
    if not "pid" in entry:
        continue

    pid = entry["pid"]
    if not pid in pids:
        logger.info("skipping project {}".format(pid))
        continue

    if "stop" in entry:
        base_stop = dateutil.parser.parse(entry["stop"])
        currently_running = False
    else:
        logger.warn("using current date/time for entry that is currently still running");
        now = datetime.now()
        base_stop = now.astimezone(get_localzone())
        currently_running = True

    start = dateutil.parser.parse(entry["start"]).replace(second=0, microsecond=0)
    stop = base_stop.replace(second=0, microsecond=0)

    delta = start - previous_stop if previous_stop else None
    new_entry = not previous_stop or (delta > GAP if delta else None)

    logger.debug("previous stop: {}, start: {}, stop: {}, gap: {}, is new entry: {}".format(
        previous_stop.astimezone(get_localzone()) if previous_stop else None,
        start.astimezone(get_localzone()),
        stop.astimezone(get_localzone()),
        delta,
        new_entry
    ))

    if new_entry:
        append_result()

        previous_start = start

    previous_stop = stop
    previous_currently_running = currently_running

append_result()


def format_datetime(date_time):
    if date_time:
        local_date_time = date_time.astimezone(get_localzone())
        date = local_date_time.strftime("%m/%d/%y").lstrip("0")
        return "{} {}".format(date, format_time(date_time))

    return "-"


def format_weekday(date_time):
    if date_time:
        local_date_time = date_time.astimezone(get_localzone())
        return local_date_time.strftime("%A").ljust(9)

    return "-"


def format_time(date_time):
    if date_time:
        local_date_time = date_time.astimezone(get_localzone())
        am_pm = local_date_time.strftime("%p").upper()[0]
        time = local_date_time.strftime("%I%M").lstrip("0")
        return "{}{}".format(time, am_pm)

    return "-"


def format_delta(start, stop):
    if not start or not stop:
        return "-"

    delta = stop - start

    minutes, seconds = divmod(delta.seconds, 60)
    decimal = minutes / 60
    return "{:.2f}".format(decimal).lstrip("0")


print()
print("                Actual  Actual  Actual  Punch")
print("Day             In Date In      Out     Hours")
print("--------------- ------- ------- ------- -----")
total_delta = timedelta(0)
for result in results:
    rounded_start = result["start"]
    rounded_stop = result["stop"]
    delta = rounded_stop - rounded_start
    print("{}\t{}\t{}{}\t{}".format(
        format_weekday(rounded_start),
        format_datetime(rounded_start),
        format_time(rounded_stop),
        "*" if result["running"] else "",
        format_delta(rounded_start, rounded_stop)
    ))

    total_delta += (rounded_stop - rounded_start)

print()
print("{} entries".format(len(results)))
print("total: {0:.2f} hours (decimal)"
      .format(total_delta.days * 24 + total_delta.seconds / 3600))
