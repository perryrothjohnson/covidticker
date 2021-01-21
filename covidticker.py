import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from Adafruit_IO import Client, RequestError, Feed
import time

# global flags
print_inline = False
print_table = True

# Johns Hopkins api -----------------------------------------------------------
if print_inline:
    print("\nJohns Hopkins:")
else:
    print("\npulling from Johns Hopkins api...")
# get latest date
api_response = requests.get('https://covid-19.datasettes.com/covid.json?sql=select+max(day)+from+johns_hopkins_csse_daily_reports+where+country_or_region=%27US%27')
latest_date = api_response.json()['rows'][0][0]
api_US_deaths = 'https://covid-19.datasettes.com/covid.json?sql=select+sum(deaths)+from+johns_hopkins_csse_daily_reports+where+country_or_region=%27US%27+and+day=%27' + latest_date + '%27'
api_response = requests.get(api_US_deaths)
us_deaths = int(float(api_response.json()['rows'][0][0]))
if print_inline:
    print("US deaths:", us_deaths)
api_world_deaths = 'https://covid-19.datasettes.com/covid.json?sql=select+sum(deaths)+from+johns_hopkins_csse_daily_reports+where+day=%27' + latest_date + '%27'
api_response = requests.get(api_world_deaths)
world_deaths = int(float(api_response.json()['rows'][0][0]))
if print_inline:
    print("World deaths:", world_deaths)
johnshopkins = pd.Series([world_deaths, us_deaths], index=['world', 'US'], name='Johns Hopkins api')

def jhu_data_url(year, month, day, region='US'):
    date = '{:02}'.format(month) + '-' + '{:02}'.format(day) + '-' + '{:04}'.format(year)
    if region == 'US':
        JHU_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/' + date + '.csv'
    elif region == 'world':
        JHU_URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports/' + date + '.csv'
    else:
        JHU_URL = None
        raise Exception("got unexpected region for jhu_data_url()")
    return JHU_URL

# Johns Hopkins github; pandas
if print_inline:
    print("\nJohns Hopkins github-pandas:")
else:
    print("pulling from Johns Hopkins github with pandas...")
# get US deaths
y = time.localtime()[0]
m = time.localtime()[1]
d = time.localtime()[2] + 1
jhu_csvfile_exists = False
while not jhu_csvfile_exists:
    JHU_DATA_SOURCE = jhu_data_url(y,m,d,region='US')
    test_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
    if print_inline:
        print("  ...fetching text for", test_date)
    r = requests.get(jhu_data_url(y,m,d))
    if r.status_code == 200:
        if print_inline:
            print("     found data for this date!")
        jhu_csvfile_exists = True
    else:
        if print_inline:
            print("     data doesn't exist for this date; trying again...")
        if int(d) > 1:
            d -= 1
        elif int(m) > 1:
            m -= 1
            d = 31
        else:
            y -= 1
            m = 12
            d = 31
r.close()
latest_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
if print_inline:
    print(' ',latest_date)
df = pd.read_csv(JHU_DATA_SOURCE)
us_deaths = sum(df['Deaths'])
if print_inline:
    print("US deaths:", us_deaths)
# get world deaths
y = time.localtime()[0]
m = time.localtime()[1]
d = time.localtime()[2] + 1
jhu_csvfile_exists = False
while not jhu_csvfile_exists:
    JHU_DATA_SOURCE = jhu_data_url(y,m,d,region='world')
    test_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
    if print_inline:
        print("  ...fetching text for", test_date)
    r = requests.get(jhu_data_url(y,m,d))
    if r.status_code == 200:
        if print_inline:
            print("     found data for this date!")
        jhu_csvfile_exists = True
    else:
        if print_inline:
            print("     data doesn't exist for this date; trying again...")
        if int(d) > 1:
            d -= 1
        elif int(m) > 1:
            m -= 1
            d = 31
        else:
            y -= 1
            m = 12
            d = 31
r.close()
latest_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
if print_inline:
    print(' ',latest_date)
df = pd.read_csv(JHU_DATA_SOURCE)
world_deaths = sum(df['Deaths'])
if print_inline:
    print("World deaths:", world_deaths)
johnshopkins_github_pandas = pd.Series([world_deaths, us_deaths], index=['world', 'US'], name='Johns Hopkins github')


# COVID Tracking Project ------------------------------------------------------
if print_inline:
    print("\nCOVID Tracking Project:")
else:
    print("pulling from COVID Tracking project...")
api_response = requests.get('https://api.covidtracking.com/v1/us/current.json')
us_deaths = int(float(api_response.json()[0]['death']))
if print_inline:
    print("US deaths:", us_deaths)
api_response = requests.get('https://api.covidtracking.com/v1/states/ca/current.json')
ca_deaths = int(float(api_response.json()['death']))
if print_inline:
    print("CA deaths:", ca_deaths)
covidtrackingproject = pd.Series([us_deaths, ca_deaths], index=['US', 'CA'], name='COVID Tracking Project')

# CDC -------------------------------------------------------------------------
if print_inline:
    print("\nCDC:")
else:
    print("pulling from the CDC...")
# get latest date
api_response = requests.get('https://data.cdc.gov/resource/9mfq-cb36.json?$select=max(submission_date)')
try:
    latest_date = api_response.json()[0]['max_submission_date'][:10]
    api_US_deaths = 'https://data.cdc.gov/resource/9mfq-cb36.json?submission_date=' + latest_date + '&$select=sum(tot_death)'
    api_response = requests.get(api_US_deaths)
    us_deaths = int(float(api_response.json()[0]['sum_tot_death']))
    if print_inline:
        print("US deaths:", us_deaths)
    api_response = requests.get('https://data.cdc.gov/resource/9mfq-cb36.json?state=CA&$select=max(tot_death)')
    ca_deaths = int(float(api_response.json()[0]['max_tot_death']))
except:
    print("...error with CDC data!!!")
    us_deaths = None
    ca_deaths = None
if print_inline:
    print("CA deaths:", ca_deaths)
cdc = pd.Series([us_deaths, ca_deaths], index=['US', 'CA'], name='CDC')

# WHO -------------------------------------------------------------------------
if print_inline:
    print("\nWHO:")
else:
    print("pulling from the WHO...")
api_response = requests.get('https://worldhealthorg.shinyapps.io/covid/_w_e3a749be/#tab-8990-1')
soup = BeautifulSoup(api_response.text, 'html.parser')
#  make sure we grabbed the data correctly and don't have an empty list
while len(soup.select('span')) == 0:
    print("  ...got an empty list, trying again...")
    api_response = requests.get('https://worldhealthorg.shinyapps.io/covid/_w_e3a749be/#tab-8990-1')
    soup = BeautifulSoup(api_response.text, 'html.parser')
else:
    world_deaths = int(float(soup.select('span')[25].text.strip()[:-7].replace(' ', '').replace(',', '')))
if print_inline:
    print("World deaths:", world_deaths)
who = pd.Series([world_deaths], index=['world'], name='WHO')

# LA Times api ----------------------------------------------------------------
if print_inline:
    print("\nLA Times:")
else:
    print("pulling from the LA Times api...")
api_response = requests.get('https://covid-19.datasettes.com/covid/latimes_county_totals.json?county=Los+Angeles')
la_deaths = int(float(api_response.json()['rows'][0][5]))
if print_inline:
    print("LA County deaths:", la_deaths)
api_response = requests.get('https://covid-19.datasettes.com/covid/latimes_state_totals.json')
ca_deaths = int(float(api_response.json()['rows'][0][3]))
if print_inline:
    print("CA deaths:", ca_deaths)
latimes = pd.Series([la_deaths, ca_deaths], index=['LA county', 'CA'], name='LA Times api')

# LA Times github; pandas
if print_inline:
    print("\nLA Times github-pandas:")
else:
    print("pulling from the LA Times github with pandas...")
URL = 'https://raw.githubusercontent.com/datadesk/california-coronavirus-data/master/latimes-county-totals.csv'
df = pd.read_csv(URL)
latest_date = df['date'][0] # date is formatted YYYY-MM-DD
# print(' ',latest_date)
la_deaths = int(df[(df['county'] == 'Los Angeles') & (df['date'] == latest_date)]['deaths'])
if print_inline:
    print("LA County deaths:", la_deaths)
ca_deaths = sum(df[df['date'] == latest_date]['deaths'])
latimes_github_pandas = pd.Series([la_deaths, ca_deaths], index=['LA county', 'CA'], name='LA Times github')


# CA Dept of Public Health ----------------------------------------------------
if print_inline:
    print("\nCA State:")
else:
    print("pulling from California Department of Public Health...")
api_response = requests.get('https://covid19.ca.gov/state-dashboard/')
soup = BeautifulSoup(api_response.text, 'html.parser')
ca_deaths = int(float(soup.find(id='total-deaths-number').text.strip().replace(',', '').replace(' total','')))
if print_inline:
    print("CA deaths:", ca_deaths)
api_LA_deaths = 'https://data.ca.gov/api/3/action/datastore_search?resource_id=926fd08f-cc91-4828-af38-bd45de97f8c3&sort=date+desc&q=Los+Angeles&limit=1'
api_response = requests.get(api_LA_deaths)
la_deaths = int(float(api_response.json()['result']['records'][0]['totalcountdeaths']))
if print_inline:
    print("LA County deaths:", la_deaths)
california = pd.Series([ca_deaths, la_deaths], index=['CA', 'LA county'], name='CDPH')

if print_inline:
    print("")

# save all the data into a table, then transpose it to display sources as rows and death regions as columns
df = pd.concat([
    johnshopkins_github_pandas,
    cdc,
    latimes_github_pandas,
    california,
    who,
    covidtrackingproject,
    johnshopkins,
    latimes
    ], axis=1).T
df = df.rename(columns={
    "world": "world", 
    "US": "United States",
    "CA": "California",
    "LA county": "LA county"
    })
df = df.replace(np.nan, '', regex=True)
pd.options.display.float_format = '{:,.0f}'.format
if print_table:
    print("\nlatest COVID-19 deaths by region, across different data sources:\n")
    print(df)
    print("")

# check for errors in US data ... if JHU data is > 10% off from CDC data, display CDC instead
try:
    if df['United States'].loc['Johns Hopkins github'] > 1.1*(df['United States'].loc['CDC']):
        print('{:7,.0f}'.format(df['United States'].loc['CDC']),  "dead in United States (CDC)")
    else:
        print('{:7,.0f}'.format(df['United States'].loc['Johns Hopkins github']),  "dead in United States (JHU)")
except:
    print('{:7,.0f}'.format(df['United States'].loc['CDC']),  "dead in United States (CDC)")

# check for errors in LA county data ... if LA Times data is > 10% off from CDPH data, display CDPH instead
try:
    if df['LA county'].loc['LA Times github'] > 1.1*(df['LA county'].loc['CDPH']):
        print('{:7,.0f}'.format(df['LA county'].loc['CDPH']),     "dead in LA county     (CDPH)")
    else:
        print('{:7,.0f}'.format(df['LA county'].loc['LA Times github']),     "dead in LA county     (LAT)")
except:
    print('{:7,.0f}'.format(df['LA county'].loc['CDPH']),     "dead in LA county     (CDPH)")
print("")

# send data to Adafruit IO ----------------------------------------------------

def send_data(us_cdc, us_jhu, la_cdph, la_lat):
    """send US and LA death data to Adafruit IO dashboard using webhooks"""
    print("sending {0} to us-deaths-cdc feed...".format(us_cdc))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/j6tLwLjmtvSioUANcJhZGmUL6f4x', json={'value': us_cdc})
    print("  data sent!")

    print("sending {0} to us-deaths-jhu feed...".format(us_jhu))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/rBqBo7PagWriXn1Mn1jpQs9WjsdT', json={'value': us_jhu})
    print("  data sent!")

    print("sending {0} to la-deaths-cdph feed...".format(la_cdph))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/2UEJ6dCJDWAvvGJgT3RVxNNUkMk8', json={'value': la_cdph})
    print("  data sent!")

    print("sending {0} to la-deaths-lat feed...".format(la_lat))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/DPAXi8YPfagpA8c82QXSPPx6ott8', json={'value': la_lat})
    print("  data sent!")

send_data(
    us_cdc=int(df['United States'].loc['CDC']),
    us_jhu=int(df['United States'].loc['Johns Hopkins github']),
    la_cdph=int(df['LA county'].loc['CDPH']),
    la_lat=int(df['LA county'].loc['LA Times github'])
    )
