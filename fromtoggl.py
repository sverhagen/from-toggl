import logging
import os
from datetime import date, timedelta, datetime

import dateutil.parser
import requests
from tzlocal import get_localzone

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__package__)

# ##### CONFIGURATION START #####
CLIENT_ID = 34710800
GAP = timedelta(minutes=10)
ROUNDING_ACCURACY = timedelta(minutes=5)
START_DATE = date(2018, 1, 8)
# ##### CONFIGURATION END #####

ENVIRONMENT_VARIABLE_TOGGL_API_TOKEN = "TOGGL_API_TOKEN"


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

start_date_string = "{}T00%3A00%3A00%2B00%3A00".format(START_DATE.isoformat())

response = requests.get(
    "https://www.toggl.com/api/v8/time_entries?start_date={}".format(start_date_string),
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
    if previous_start:
        results.append({
            "start": floor_dt(previous_start),
            "stop": ceil_dt(previous_stop)
        })


for entry in data:
    pid = entry["pid"]
    if not entry["pid"] in pids:
        logger.info("skipping project {}".format(pid))
        continue

    start = dateutil.parser.parse(entry["start"]).replace(second=0, microsecond=0)
    stop = dateutil.parser.parse(entry["stop"]).replace(second=0, microsecond=0)

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
for result in results:
    rounded_start = result["start"]
    rounded_stop = result["stop"]
    delta = rounded_stop - rounded_start
    print("{}\t{}\t{}\t{}".format(
        format_weekday(rounded_start),
        format_datetime(rounded_start),
        format_time(rounded_stop),
        format_delta(rounded_start, rounded_stop)
    ))
