"""
A wall-mounted ticker, which updates daily with the total number of 
COVID-19 deaths for the United States and Los Angeles county.

Author: Perry Roth-Johnson
Last modified: 24 Dec 2020

code was built on the following examples:
---
esp32spi_simpletest.py
https://learn.adafruit.com/adafruit-matrixportal-m4/internet-connect
---
metro_matrix_clock.py
https://learn.adafruit.com/network-connected-metro-rgb-matrix-clock/code-the-matrix-clock
---
adafruit_io_simpletest.py
https://learn.adafruit.com/adafruit-io-basics-airlift/circuitpython
---
matrix_sprite_animation_player.py
https://learn.adafruit.com/tombstone-matrix-portal/code-the-sprite-sheet-animation-display
---

todo (v19):
change secrets.py with info from new wifi router we buy for exhibit
---optional---
add logging to hard disk in case of crash?
install heat sink and/or cooling fan onto Matrix Portal board?
implement DATA_LOCATION variables to traverse JSON instead of hardcoding in pull_data()?
delete horizontal space after commas in Vera font??
"""

import time
import board
import displayio
import terminalio
import adafruit_requests as requests
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text.label import Label
from adafruit_io.adafruit_io import IO_HTTP, AdafruitIO_RequestError
from digitalio import DigitalInOut, Pull
from adafruit_debouncer import Debouncer
from adafruit_bitmap_font import bitmap_font

DEBUG = False
FANCY_FONT = True

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# setup data sources to pull from ---------------------------------------------
CDC_LATEST_DATE_SOURCE = 'https://data.cdc.gov/resource/9mfq-cb36.json?$select=max(submission_date)'
def cdc_data(date):
    CDC_DATA_SOURCE = 'https://data.cdc.gov/resource/9mfq-cb36.json?submission_date=' + date + '&$select=sum(tot_death)'
    return CDC_DATA_SOURCE
# CDC_DATA_LOCATION = [0, 'sum_tot_death']

CDPH_DATA_SOURCE = 'https://data.ca.gov/api/3/action/datastore_search?resource_id=926fd08f-cc91-4828-af38-bd45de97f8c3&sort=date+desc&q=Los+Angeles&limit=1'
# CDPH_DATA_LOCATION = ['result', 'records', 0, 'totalcountdeaths']

JHU_LATEST_DATE_SOURCE = 'https://covid-19.datasettes.com/covid.json?sql=select+max(day)+from+johns_hopkins_csse_daily_reports+where+country_or_region=%27US%27'
def jhu_data(date):
    JHU_DATA_SOURCE = ('https://covid-19.datasettes.com/covid.json?sql=select+sum(deaths)+from+johns_hopkins_csse_daily_reports+where+country_or_region=%27US%27+and+day=%27' + date + '%27')
    return JHU_DATA_SOURCE
# JHU_DATA_LOCATION = ['rows', 0, 0]

LAT_DATA_SOURCE = 'https://covid-19.datasettes.com/covid.json?sql=select+date%2C+county%2C+deaths+from+latimes_county_totals+where+%22county%22+%3D+%3Ap0+limit+1&p0=Los+Angeles'
# LAT_DATA_LOCATION = ['rows', 0, 2]

# setup the LED matrix display ------------------------------------------------
matrix = Matrix()
display = matrix.display

# drawing setup
group = displayio.Group(max_size=4)  # create a Group
bitmap = displayio.Bitmap(64, 32, 2)  # create a bitmap object, width, height, bit depth
color = displayio.Palette(4)  # create a color palette
color[0] = 0x000000  # black background
color[1] = 0xFF0000  # red
# color[2] = 0xCC4000  # amber
color[2] = 0x0000FF  # blue
# color[3] = 0x85FF00  # greenish
color[3] = 0x120766  # custom blue
std_font = terminalio.FONT
if FANCY_FONT:
    vera_font = bitmap_font.load_font("/BitstreamVeraSansMono-Bold-14.bdf")
    glyphs = b"0123456789, colr"
    vera_font.load_glyphs(glyphs)
 
# create a TileGrid using the Bitmap and Palette
tile_grid = displayio.TileGrid(bitmap, pixel_shader=color)
group.append(tile_grid)  # add the TileGrid to the Group
display.show(group)
top_label = Label(std_font, max_glyphs=12)
bottom_label = Label(std_font, max_glyphs=12)

# define functions ------------------------------------------------------------

def pull_data(us_source='CDC', la_source='CDPH'):
    """
    pull data for deaths in US and LA county.

    us_source = 'CDC' or 'JHU'
    la_source = 'CDPH' or 'LAT'

    where... 
    CDC (Centers for Disease Control)
    JHU (Johns Hopkins University)
    CDPH (California Department of Public Health)
    LAT (Los Angeles Times)

    """
    if us_source == 'CDC':
        print("\npulling data from CDC...")
        try:
            # get latest date
            r = requests.get(CDC_LATEST_DATE_SOURCE)
            latest_date = r.json()[0]['max_submission_date'][:10]
            # get US death count
            CDC_DATA_SOURCE = cdc_data(latest_date)
            r = requests.get(CDC_DATA_SOURCE)
            us_deaths = int(float(r.json()[0]['sum_tot_death']))
        except:
            print("  ...error with CDC data!")
            us_deaths = 0
            latest_date = None
    if us_source == 'JHU':
        try:
            print("\npulling data from Johns Hopkins...")
            # get latest date
            r = requests.get(JHU_LATEST_DATE_SOURCE)
            latest_date = r.json()['rows'][0][0]
            # get US death count
            JHU_DATA_SOURCE = jhu_data(latest_date)
            r = requests.get(JHU_DATA_SOURCE)
            us_deaths = int(float(r.json()['rows'][0][0]))
        except:
            print("  ...error with JHU data!")
            us_deaths = 0
            latest_date = None
    print("-" * 40)
    print('{:9,}'.format(us_deaths))
    print("dead in US")
    print("as of", latest_date)
    print("-" * 40)
    r.close()

    if la_source == 'CDPH':
        print("\npulling data from CDPH...")
        try:
            r = requests.get(CDPH_DATA_SOURCE)
            latest_date = r.json()['result']['records'][0]['date'][:10]
            la_deaths = int(float(r.json()['result']['records'][0]['totalcountdeaths']))
        except:
            print("  ...error with CDPH data!")
            la_deaths = 0
            latest_date = None
    if la_source == 'LAT':
        print("\npulling data from LA Times...")
        try:
            r = requests.get(LAT_DATA_SOURCE)
            latest_date = r.json()['rows'][0][0]
            la_deaths = int(float(r.json()['rows'][0][2]))
        except:
            print("  ...error with LAT data!")
            la_deaths = 0
            latest_date = None
    print("-" * 40)
    print('{:9,}'.format(la_deaths))
    print("dead in LA county")
    print("as of", latest_date)
    print("-" * 40)
    r.close()

    return (us_deaths, la_deaths)

def check_data_for_errors(us_cdc, us_jhu, us_last, la_cdph, la_lat, la_last, error_factor=0.1):
    """
    check US and LA death counts against secondary sources, and compare to
    an error factor (default: 10%)

    if US deaths reported by JHU are off by >10% from CDC, use CDC data instead
    if LA deaths reported by LAT are off by >10% from CDPH, use CDPH data instead

    parameters
    ----------
    us_cdc : US deaths, reported by the CDC
    us_jhu : US deaths, reported by Johns Hopkins
    us_last : US deaths, last recorded by this code
    la_cdph : LA county deaths, reported by CA Dept of Public Health
    la_lat : LA county deaths, reported by LA Times
    la_last : LA county deaths, last recorded by this code
    error_factor : number between 0 and 1 used to check for errors (0.1 = 10%)

    """
    # check US data
    print("\nchecking US death data...")
    if us_cdc == 0 and us_jhu == 0:
        if us_last != 0:
            print("  we have bad data for CDC and JHU, so fall back to last recorded data")
            us_deaths = us_last
        else:
            raise Exception("ERROR: bad US data for CDC, JHU, and last recording")
    elif us_cdc == 0 and us_jhu != 0:
        print("  we have bad data for CDC, so use JHU instead")
        us_deaths = us_jhu
    elif us_cdc != 0 and us_jhu == 0:
        print("  we have bad data for JHU, so use CDC instead")
        us_deaths = us_cdc
    else:
        # we have nonzero US data for both sources
        print("  ...checking that US data is not off by a factor of", error_factor)
        if abs(us_cdc - us_jhu) > error_factor*us_cdc:
            print('  display CDC data for US deaths; error exceeded')
            us_deaths = us_cdc
        else:
            print('  display Johns Hopkins data for US deaths; error not exceeded')
            us_deaths = us_jhu

    # check LA data
    print("\nchecking LA death data...")
    if la_cdph == 0 and la_lat == 0:
        if la_last != 0:
            print("  we have bad data for CDPH and LAT, so fall back to last recorded data")
            la_deaths = la_last
        else:
            raise Exception("ERROR: bad LA data for CDPH, LAT, and last recording")
    elif la_cdph == 0 and la_lat != 0:
        print("  we have bad data for CDPH, so use LAT instead")
        la_deaths = la_lat
    elif la_cdph != 0 and la_lat == 0:
        print("  we have bad data for LAT, so use CDPH instead")
        la_deaths = la_cdph
    else:
        # we have nonzero LA data for both sources
        print("  ...checking that LA data is not off by a factor of", error_factor)
        if abs(la_cdph - la_lat) > error_factor*la_cdph:
            print('  display CDPH data for LA county deaths; error exceeded')
            la_deaths = la_cdph
        else:
            print('  display LA Times data for LA county deaths; error not exceeded')
            la_deaths = la_lat
    return (us_deaths, la_deaths)

def display_data(top_text=None, bottom_text=None, top_color=color[1], bottom_color=color[2], font='std'):
    """display death counts on LED matrix display"""
    if font == 'vera':
        top_label.font = vera_font
        bottom_label.font = vera_font
    else:
        top_label.font = std_font
        bottom_label.font = std_font

    # US deaths
    top_label.color = top_color
    if font == 'vera':
        top_label.text = '{:7,}'.format(top_text)
    else:
        top_label.text = '{:9,}'.format(top_text)
    tbbx, tbby, tbbw, tbbh = top_label.bounding_box
    if font == 'vera':
        # center the label
        top_label.x = round(display.width / 2 - tbbw / 2)
        top_label.y = 7
    else:
        top_label.x = 3
        top_label.y = 7
    if DEBUG:
        print("Label bounding box: {},{},{},{}".format(tbbx, tbby, tbbw, tbbh))
        print("Label x: {} y: {}".format(top_label.x, top_label.y))

    # LA deaths
    bottom_label.color = bottom_color
    if font == 'vera':
        bottom_label.text = '{:7,}'.format(bottom_text)
    else:
        bottom_label.text = '{:9,}'.format(bottom_text)
    bbbx, bbby, bbbw, bbbh = bottom_label.bounding_box
    if font == 'vera':
        # center the label
        bottom_label.x = round(display.width / 2 - bbbw / 2)
        bottom_label.y = (7 + 17)
    else:
        bottom_label.x = top_label.x
        bottom_label.y = (7 + 16)
    if DEBUG:
        print("Label bounding box: {},{},{},{}".format(bbbx, bbby, bbbw, bbbh))
        print("Label x: {} y: {}".format(bottom_label.x, bottom_label.y))

def send_data(us_cdc, us_jhu, la_cdph, la_lat):
    """send US and LA death data to Adafruit IO dashboard"""
    print("sending {0} to us-deaths-cdc feed...".format(us_cdc))
    io.send_data(us_cdc_feed["key"], us_cdc)
    print("  data sent!")

    print("sending {0} to us-deaths-jhu feed...".format(us_jhu))
    io.send_data(us_jhu_feed["key"], us_jhu)
    print("  data sent!")

    print("sending {0} to la-deaths-cdph feed...".format(la_cdph))
    io.send_data(la_cdph_feed["key"], la_cdph)
    print("  data sent!")

    print("sending {0} to la-deaths-lat feed...".format(la_lat))
    io.send_data(la_lat_feed["key"], la_lat)
    print("  data sent!")

def get_color():
    """get color picked on Adafruit IO dashboard"""
    # Retrieve data value from the feed
    print("\nretrieving data from LED color feed...")
    received_data = io.receive_data(led_feed["key"])
    received_color_str = '0x' + received_data["value"][1:]
    received_color_hex = int(received_color_str)
    print("Data from LED color feed: ", received_data["value"], "(", received_color_str, ")")
    return received_color_hex

def sync_time(display_LED_text=False):
    """sync the clock on this board with internet time from Adafruit IO"""
    try:
        print("\nobtaining time from adafruit.io server...")
        if display_LED_text:
            display_data('getting', 'time...')
        network.get_local_time()
        current_time = time.monotonic()
    except RuntimeError as e:
        print("Unable to obtain time from Adafruit IO, retrying - ", e)
    return current_time

# initialize the display labels -----------------------------------------------
us_deaths = 'loading...'
la_deaths = 'loading...'
group.append(top_label)
group.append(bottom_label)
display_data(us_deaths, la_deaths)
time.sleep(5)

# connect to the internet -----------------------------------------------------
print("setting up network...")
network = Network(status_neopixel=board.NEOPIXEL, debug=False)
is_connected = False
while not is_connected:
    try:
        print("trying to connect to AP...")
        display_data('connecting', 'wifi...')
        network.connect()
        is_connected = True
    except RuntimeError as e:
        print("could not connect to AP, retrying: ", e)
        continue
if is_connected:
    print("...connnected to internet!")
    display_data('wifi', 'good!!!')
time.sleep(2)

# connect to Adafruit IO dashboard --------------------------------------------
# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

# Initialize an Adafruit IO HTTP API object
io = IO_HTTP(aio_username, aio_key, requests)

# setup feeds to talk to Adafruit IO dashboard
if not DEBUG:
    print("\nconnecting to Adafruit IO, setting up feeds...")
    display_data('connecting', 'AdafruitIO')
    try:
        # Get the 'la-deaths-cdph' feed from Adafruit IO
        la_cdph_feed = io.get_feed("la-deaths-cdph")
        print("  got feed 1 of 5...")
        display_data('AIO feed', '1/5...')
    except AdafruitIO_RequestError:
        # If no 'la-deaths-cdph' feed exists, create one
        la_cdph_feed = io.create_new_feed("la-deaths-cdph")

    try:
        # Get the 'la-deaths-lat' feed from Adafruit IO
        la_lat_feed = io.get_feed("la-deaths-lat")
        print("  got feed 2 of 5...")
        display_data('AIO feed', '2/5...')
    except AdafruitIO_RequestError:
        # If no 'la-deaths-lat' feed exists, create one
        la_lat_feed = io.create_new_feed("la-deaths-lat")

    try:
        # Get the 'us-deaths-cdc' feed from Adafruit IO
        us_cdc_feed = io.get_feed("us-deaths-cdc")
        print("  got feed 3 of 5...")
        display_data('AIO feed', '3/5...')
    except AdafruitIO_RequestError:
        # If no 'us-deaths-cdc' feed exists, create one
        us_cdc_feed = io.create_new_feed("us-deaths-cdc")

    try:
        # Get the 'us-deaths-jhu' feed from Adafruit IO
        us_jhu_feed = io.get_feed("us-deaths-jhu")
        print("  got feed 4 of 5...")
        display_data('AIO feed', '4/5...')
    except AdafruitIO_RequestError:
        # If no 'us-deaths-jhu' feed exists, create one
        us_jhu_feed = io.create_new_feed("us-deaths-jhu")

    try:
        # Get the 'LED-color' feed from Adafruit IO
        led_feed = io.get_feed("led-color")
        print("  got feed 5 of 5...")
        display_data('AIO feed', '5/5...')
    except AdafruitIO_RequestError:
        # If no 'led-color' feed exists, create one
        led_feed = io.create_new_feed("led-color")

time.sleep(1)

# setup buttons ---------------------------------------------------------------
if not DEBUG:
    pin_down = DigitalInOut(board.BUTTON_DOWN)
    pin_down.switch_to_input(pull=Pull.UP)
    button_down = Debouncer(pin_down)

    pin_up = DigitalInOut(board.BUTTON_UP)
    pin_up.switch_to_input(pull=Pull.UP)
    button_up = Debouncer(pin_up)

# initialize counters ---------------------------------------------------------
run_num = 0
prv_hour = 0
prv_min = 0
prv_us = 0
prv_la = 0
color_mode = False
start_time = None
color_run_num = 0
# synchronize the board's clock to the internet
if not DEBUG:
    start_time = sync_time(display_LED_text=True)

# main loop -------------------------------------------------------------------
while True:
    # update the state of the buttons
    if not DEBUG:
        button_down.update()
        button_up.update()
        if button_down.fell:
            # if button_down pushed, go into color_mode
            color_mode = True
            print("***BUTTON_DOWN PUSHED!!!***")
            print('color_mode =', color_mode)
        if button_up.fell:
            # if button_up pushed, exit color_mode
            color_mode = False
            color_run_num = 0
            print("***BUTTON_UP PUSHED!!!***")
            print('color_mode =', color_mode)
    
    if color_mode and (not DEBUG):
        display_data(us_deaths, 'color', color[3], color[3], font='vera')
        color_run_num += 1
        new_color = get_color()
        # if a new color is detected or timeout, exit color mode
        if new_color != color[3] or color_run_num > 4:
            color_run_num = 0
            color_mode = False
            # if a new color is detected, updated the LED display color
            if new_color != color[3]:
                color[3] = new_color
            display_data(us_deaths, la_deaths, color[3], color[3], font='vera')
        time.sleep(1) # wait 1 second
    else:
        # pull new data on first run, then every hour after that
        if time.localtime()[3] != prv_hour:
            try:
                print("\nnew hour, fetching new data...")
                print(str(time.localtime()[3]) + ':' + str(time.localtime()[4]))
                print("run #", run_num)
                # at 9am every day, re-sync the board's clock
                if time.localtime()[3] == 9:
                    sync_time(display_LED_text=False)
                if run_num == 0:
                    display_data('get CDC...', 'get CDPH...')
                (cdc_count, cdph_count) = pull_data(us_source='CDC', la_source='CDPH')
                if run_num == 0:
                    display_data('get JHU...', 'get LAT...')
                (jhu_count, lat_count) = pull_data(us_source='JHU', la_source='LAT')
                (us_deaths, la_deaths) = check_data_for_errors(
                    us_cdc=cdc_count,
                    us_jhu=jhu_count,
                    us_last=prv_us,
                    la_cdph=cdph_count,
                    la_lat=lat_count,
                    la_last=prv_la)
                if run_num == 0:
                    new_color = get_color()
                    # if a new color is detected, update the LED display color
                    if new_color != color[3]:
                        color[3] = new_color
                display_data(us_deaths, la_deaths, color[3], color[3], font='vera')
                if not DEBUG:
                    send_data(
                        us_cdc=cdc_count,
                        us_jhu=jhu_count,
                        la_cdph=cdph_count,
                        la_lat=lat_count)
                # prv_hour = time.localtime()[3]
                # prv_min = time.localtime()[4]
                prv_us = us_deaths
                prv_la = la_deaths
                # run_num +=1
            except RuntimeError as e:
                print("Some error occurred, retrying! - ", e)
            finally:
                # make sure we update the time, even if the 9am clock sync fails
                prv_hour = time.localtime()[3]
                prv_min = time.localtime()[4]
                run_num += 1
        else:
            # after exiting color_mode, we don't need to update the data...
            # ...just display the last stored data
            display_data(us_deaths, la_deaths, color[3], color[3], font='vera')

    if (not DEBUG) and (time.monotonic() < start_time + (10 * 60)):
        # during the first 10 min of uptime, run the main loop every 1 sec
        time.sleep(1) # wait 1 second
    else:
        # afterwards, only run the main loop every 5 min
        time.sleep(5 * 60) # wait 5 minutes
