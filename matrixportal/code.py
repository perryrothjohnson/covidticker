"""
A wall-mounted ticker, which updates daily with the total number of 
COVID-19 deaths for the United States and Los Angeles county.

author:         Perry Roth-Johnson
last modified:  1 Feb 2021
version:        2.11

---todo---
change secrets.py with info from new wifi router we buy for exhibit
install heat sink and/or cooling fan onto Matrix Portal board?
"""

### monitor free memory ###
def stat(lbl, send_to_AIO=False):
    mf = gc.mem_free() / 1024
    if send_to_AIO:
        mqtt_client.publish(logging_feed, mf)
    print('%s %g' % (lbl, mf))
import gc
stat('gc')

import time
import board
import busio
from digitalio import DigitalInOut
import neopixel
from adafruit_esp32spi import adafruit_esp32spi, adafruit_esp32spi_wifimanager
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import displayio
import terminalio
from adafruit_matrixportal.matrix import Matrix
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font

stat('imports')

### global variables ###

DEBUG = False
DEBUG_LOOP = False
FANCY_FONT = True
feeds = {
    'still_alive' : None,
    'mem_free' : None,
    'loop_delay' : None,
    'led_color': None,  # same as color[3]
    'us_toggle': None,
    'la_toggle': None,
    'cdph_count': None,
    'lat_count': None,
    'cdc_count': None,
    'jhu_count': None
}

stat('global variables')

### setup LED matrix display ###

matrix = Matrix()
display = matrix.display

# drawing setup
group = displayio.Group(max_size=4)  # create a Group
bitmap = displayio.Bitmap(64, 32, 2)  # create a bitmap object, width, height, bit depth
color = displayio.Palette(4)  # create a color palette
color[0] = 0x000000  # black background
color[1] = 0xFF0000  # red
color[2] = 0x0000FF  # blue
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

# initialize the display labels
group.append(top_label)
group.append(bottom_label)

stat('setup LED matrix display')

# ### WiFi ###

# Get wifi/Adafruit IO details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi/AIO secrets are kept in secrets.py, please add them there!")
    raise

# If you are using a board with pre-defined ESP32 Pins:
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
status_light = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0.2)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, status_light)

stat('wifi')

### Feeds ###

# Setup all 8 feeds
cdph_feed = secrets["aio_username"] + "/feeds/la-deaths-cdph"
lat_feed = secrets["aio_username"] + "/feeds/la-deaths-lat"
cdc_feed = secrets["aio_username"] + "/feeds/us-deaths-cdc"
jhu_feed = secrets["aio_username"] + "/feeds/us-deaths-jhu"
led_color_feed = secrets["aio_username"] + "/feeds/led-color"
jhu_cdc_feed = secrets["aio_username"] + "/feeds/jhu-cdc"
lat_cdph_feed = secrets["aio_username"] + "/feeds/lat-cdph"
loop_delay_feed = secrets["aio_username"] + "/feeds/loop-delay"
logging_feed = secrets["aio_username"] + "/feeds/logging"
still_alive_feed = secrets["aio_username"] + "/feeds/still-alive"

stat('feeds')

### MQTT callback methods ###

# Define callback methods which are called when events occur
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to Adafruit IO!")
    # set quality of service (QOS) level
    QOS_level = 0
    # subscribe to all changes on 4 feeds for sources of death data
    client.subscribe(cdph_feed, qos=QOS_level)
    display_data('AIO feed', '1/9')
    client.subscribe(lat_feed, qos=QOS_level)
    display_data('AIO feed', '2/9')
    client.subscribe(cdc_feed, qos=QOS_level)
    display_data('AIO feed', '3/9')
    client.subscribe(jhu_feed, qos=QOS_level)
    display_data('AIO feed', '4/9')
    # subscribe to all changes on 4 feeds for dashboard controls
    client.subscribe(led_color_feed, qos=QOS_level)
    display_data('AIO feed', '5/9')
    client.subscribe(jhu_cdc_feed, qos=QOS_level)
    display_data('AIO feed', '6/9')
    client.subscribe(lat_cdph_feed, qos=QOS_level)
    display_data('AIO feed', '7/9')
    client.subscribe(loop_delay_feed, qos=QOS_level)
    display_data('AIO feed', '8/9')
    # subscribe to all changes on 2 feeds to check if LED matrix is working
    client.subscribe(still_alive_feed, qos=QOS_level)
    display_data('AIO feed', '9/9')
    # client.subscribe(logging_feed, qos=QOS_level)
    # display_data('AIO feed', '10/10')
    time.sleep(1)

def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Listening for changes on feed", topic, "  QOS:", granted_qos)

def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from Adafruit IO!")

def message(client, topic, message):
    # This method is called when a topic the client is subscribed to
    # has a new message.
    print("New message on topic {0}: {1}".format(topic, message))

def on_still_alive_msg(client, topic, message):
    # Method called whenever user/feeds/still-alive has a new value
    # (scheduled trigger sets this feed to 0 every 30 minutes)
    print(topic, message)
    feeds['still_alive'] = int(message)
    if int(message) == 0:
        # once the Adafruit broker sends us a 0, set it back to 1
        # to tell the dashboard that the LED display is still alive
        mqtt_client.publish(still_alive_feed, 1)
        feeds['still_alive'] = 1
        print("  ...LED display is still alive!")

def on_logging_msg(client, topic, message):
    # Method called whenever user/feeds/logging has a new value
    print(topic, message)
    feeds['logging'] = float(message)

def on_loop_delay_msg(client, topic, message):
    # Method called whenever user/feeds/loop-delay has a new value
    print(topic, message)
    feeds['loop_delay'] = int(message)

def on_led_color_msg(client, topic, message):
    # Method called whenever user/feeds/led-color has a new value
    # strip leading '#' and replace with '0x'
    new_color_str = '0x' + message[1:]
    # return hex value
    new_color_hex = int(new_color_str)
    color[3] = new_color_hex
    # pull jhu-cdc and lat-cdph feeds to update toggles 
    # (and force colors to update on display)
    mqtt_client.publish("{0}/get".format(jhu_cdc_feed), "\0")
    mqtt_client.publish("{0}/get".format(lat_cdph_feed), "\0")
    print(topic, message)
    print("Data from LED color feed: " + message + " (" + new_color_str + ")")
    feeds['led_color'] = new_color_hex

def on_jhu_cdc_msg(client, topic, message):
    # Method called whenever user/feeds/jhu-cdc has a new value
    us_toggle = message
    if message == 'JHU':
        # pull JHU data to update jhu_count (and force it to display)
        mqtt_client.publish("{0}/get".format(jhu_feed), "\0")
    elif message == 'CDC':
        # pull CDC data to update cdc_count (and force it to display)
        mqtt_client.publish("{0}/get".format(cdc_feed), "\0")
    else:
        print("unexpected valued received on jhu-cdc feed")
    print(topic, message)
    feeds['us_toggle'] = us_toggle

def on_lat_cdph_msg(client, topic, message):
    # Method called whenever user/feeds/lat-cdph has a new value
    la_toggle = message
    if message == 'LAT':
        # pull LAT data to update lat_count (and force it to display)
        mqtt_client.publish("{0}/get".format(lat_feed), "\0")
    elif message == 'CDPH':
        # pull CDPH data to update cdph_count (and force it to display)
        mqtt_client.publish("{0}/get".format(cdph_feed), "\0")
    else:
        print("unexpected valued received on lat-cdph feed")
    print(topic, message)
    feeds['la_toggle'] = la_toggle

def on_la_cdph_msg(client, topic, message):
    # Method called whenever user/feeds/la-deaths-cdph has a new value
    cdph_count = int(message)
    print(topic, message)
    feeds['cdph_count'] = cdph_count

def on_la_lat_msg(client, topic, message):
    # Method called whenever user/feeds/la-deaths-lat has a new value
    lat_count = int(message)
    print(topic, message)
    feeds['lat_count'] = lat_count

def on_us_cdc_msg(client, topic, message):
    # Method called whenever user/feeds/us-deaths-cdc has a new value
    cdc_count = int(message)
    print(topic, message)
    feeds['cdc_count'] = cdc_count

def on_us_jhu_msg(client, topic, message):
    # Method called whenever user/feeds/us-deaths-jhu has a new value
    jhu_count = int(message)
    print(topic, message)
    feeds['jhu_count'] = jhu_count

stat('MQTT callback methods')

### LED matrix functions ###

def display_data(top_text=None, bottom_text=None, top_color=color[1], bottom_color=color[2], font='std', million_deaths=False):
    """display death counts on LED matrix display"""
    if font == 'vera':
        if million_deaths:
            top_label.font = std_font
            bottom_label.font = std_font
        else:
            top_label.font = vera_font
            bottom_label.font = vera_font
    else:
        top_label.font = std_font
        bottom_label.font = std_font

    # US deaths
    if top_text is not None:
        top_label.color = top_color
        if font == 'vera':
            if million_deaths:
                top_label.text = '{:9,}'.format(top_text)
            else:
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
    if bottom_text is not None:
        bottom_label.color = bottom_color
        if font == 'vera':
            if million_deaths:
                bottom_label.text = '{:9,}'.format(bottom_text)
            else:
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

stat('LED matrix functions')


# Connect to WiFi
print("Connecting to WiFi...")
display_data('connecting', 'wifi...')
wifi.connect()
print("Connected!")
display_data('wifi', 'good!!!')
time.sleep(1)

stat('wifi')
gc.collect()
stat('wifi (after gc)')

# Initialize MQTT interface with the esp interface
print("starting MQTT...")
display_data('starting', 'MQTT...')
MQTT.set_socket(socket, esp)

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    client_id="covidticker",
    log=False,
    keep_alive=60
)

# set logging priority level
# mqtt_client.attach_logger(logger_name='logging')
# mqtt_client.set_logger_level("DEBUG")

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_subscribe = subscribe
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

time.sleep(1)

stat('mqtt_client')

# Connect the client to the MQTT broker.
print("Connecting to Adafruit IO...")
display_data('connecting', 'AdafruitIO')
time.sleep(5)
mqtt_client.connect()
time.sleep(1)

stat('connect AIO', send_to_AIO=True)

# Set up a message handler for all the feeds
mqtt_client.add_topic_callback(cdph_feed, on_la_cdph_msg)
mqtt_client.add_topic_callback(lat_feed, on_la_lat_msg)
mqtt_client.add_topic_callback(cdc_feed, on_us_cdc_msg)
mqtt_client.add_topic_callback(jhu_feed, on_us_jhu_msg)
mqtt_client.add_topic_callback(led_color_feed, on_led_color_msg)
mqtt_client.add_topic_callback(jhu_cdc_feed, on_jhu_cdc_msg)
mqtt_client.add_topic_callback(lat_cdph_feed, on_lat_cdph_msg)
mqtt_client.add_topic_callback(loop_delay_feed, on_loop_delay_msg)
mqtt_client.add_topic_callback(still_alive_feed, on_still_alive_msg)
mqtt_client.add_topic_callback(logging_feed, on_logging_msg)

# initialize LED color to custom blue
feeds['led_color'] = color[3]

# initialize loop_delay to 7 seconds
feeds['loop_delay'] = 7
mqtt_client.publish(loop_delay_feed, feeds['loop_delay'])

stat('initializations', send_to_AIO=True)

# get recent values on all the feeds
mqtt_client.publish("{0}/get".format(still_alive_feed), "\0")
mqtt_client.publish("{0}/get".format(logging_feed), "\0")
mqtt_client.publish("{0}/get".format(loop_delay_feed), "\0")
mqtt_client.publish("{0}/get".format(led_color_feed), "\0")
mqtt_client.publish("{0}/get".format(jhu_cdc_feed), "\0")
mqtt_client.publish("{0}/get".format(lat_cdph_feed), "\0")
mqtt_client.publish("{0}/get".format(jhu_feed), "\0")
mqtt_client.publish("{0}/get".format(lat_feed), "\0")
mqtt_client.publish("{0}/get".format(cdc_feed), "\0")
mqtt_client.publish("{0}/get".format(cdph_feed), "\0")

stat('publishes', send_to_AIO=True)

while True:
    try:
        # check incoming subscription messages from Adafruit IO
        mqtt_client.loop()
        # print the dictionary of feeds to the screen?
        if DEBUG_LOOP:
            print('-' * 40)
            print(feeds)
        # display the top number (US deaths)
        if feeds['us_toggle'] == 'JHU':
            if not FANCY_FONT:
                display_data(top_text=feeds['jhu_count'])
            else:
                display_data(top_text=feeds['jhu_count'], top_color=feeds['led_color'], font='vera')
        elif feeds['us_toggle'] == 'CDC':
            if not FANCY_FONT:
                display_data(top_text=feeds['cdc_count'])
            else:
                display_data(top_text=feeds['cdc_count'], top_color=feeds['led_color'], font='vera')
        # display the bottom number (LA county deaths)
        if feeds['la_toggle'] == 'LAT':
            if not FANCY_FONT:
                display_data(bottom_text=feeds['lat_count'])
            else:
                display_data(bottom_text=feeds['lat_count'], bottom_color=feeds['led_color'], font='vera')
        elif feeds['la_toggle'] == 'CDPH':
            if not FANCY_FONT:
                display_data(bottom_text=feeds['cdph_count'])
            else:
                display_data(bottom_text=feeds['cdph_count'], bottom_color=feeds['led_color'], font='vera')
        # collect garbage to free up memory
        gc.collect()
        stat('main loop (try)', send_to_AIO=True)
    except:
        print("Failed to get data, retrying!\n")
        # reconnect to WiFi and Adafruit IO
        wifi.reset()
        mqtt_client.reconnect()
        stat('main loop (except)', send_to_AIO=True)
        continue
    time.sleep(feeds['loop_delay'])
