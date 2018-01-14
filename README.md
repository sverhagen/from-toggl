# from-toggl
Simple scripts to convert [Toggl](https://toggl.com/) time entries into another format. As a contractor, I track my time
in Toggl, and it's easy to export time sheets/reports, but some customers desire hours to be entered in a different
format or a different application.

Some features:
- Merge time entries when these are essentially the same block of work
- Format for _Kronos_


## Requirements

Python 3.6 is required.

## Installation

1. Clone this repository
2. Preferably create a virtual environment, but in any case install the dependencies from `requirements.txt`. E.g.:

       mkvirtualenv from-toggl -p python3.6 -r requirements.txt

3. [Get an API token from Toggl](https://toggl.com/app/profile)
4. Set the API token as the `TOGGL_API_TOKEN` environment variable. E.g.:

       export TOGGL_API_TOKEN=" 1234567890abcdef1234567890abcdef"

5. Configure the script as desired. See the `##### CONFIGURATION #####` block in `fromtoggl.py`. Set constants:

   - `CLIENT_ID`: number signifying the client ID
   - `GAP`: maximum time between two time entries to consider these the same block of work and merge them together
   - `ROUNDING_ACCURACY`: number of minutes by which to round time entries up or down (in favor of the worker, thus
   accounting for entering the office and such), e.g. 12:03 becomes 12:00  
   - `START_DATE`: start date to export time entries from 

6. Run the script:

       python fromtoggl.py

7. Enjoy the output:

                 Actual  Actual  Actual  Punch
       Day       In Date In      Out     Hours
       --------- ------- ------- ------- -----
       Monday    1/08/18 100P    350P    2.83
       Tuesday   1/09/18 900A    1145A   2.75
       Tuesday   1/09/18 130P    451P    3.35
       Wednesday 1/10/18 900A    1203P   3.05
       Wednesday 1/10/18 1249P   600P    5.18
       Thursday  1/11/18 910A    1155A   2.75
       Thursday  1/11/18 105P    600P    4.92
       Friday    1/12/18 900A    1200P   3.00
       Friday    1/12/18 113P    500P    3.78
       Friday    1/12/18 958P    124A    3.43
       Saturday  1/13/18 135A    148A    .22
