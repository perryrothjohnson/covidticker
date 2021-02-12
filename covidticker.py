import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import time

# global flags
print_table = True

# Johns Hopkins api -----------------------------------------------------------
print("\npulling from Johns Hopkins api...")
# US deaths
try:
    # get latest date
    r = requests.get('https://covid-19.datasettes.com/covid.json?sql=select+max(day)+from+johns_hopkins_csse_daily_reports+where+country_or_region=%27US%27')
    latest_date = r.json()['rows'][0][0]
    api_US_deaths = 'https://covid-19.datasettes.com/covid.json?sql=select+sum(deaths)+from+johns_hopkins_csse_daily_reports+where+country_or_region=%27US%27+and+day=%27' + latest_date + '%27'
    r = requests.get(api_US_deaths)
    us_deaths = int(float(r.json()['rows'][0][0]))
except:
    us_deaths = None
finally:
    r.close()
# world deaths
try:
    r = requests.get('https://covid-19.datasettes.com/covid.json?sql=select+sum(deaths)+from+johns_hopkins_csse_daily_reports+where+day=%27' + latest_date + '%27')
    world_deaths = int(float(r.json()['rows'][0][0]))
except:
    world_deaths = None
finally:
    r.close()
johnshopkins_api = pd.Series([world_deaths, us_deaths], index=['world', 'US'], name='JHU api')

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
print("pulling from Johns Hopkins github...")
# US deaths
try:
    y = time.localtime()[0]
    m = time.localtime()[1]
    d = time.localtime()[2] + 1
    jhu_csvfile_exists = False
    while not jhu_csvfile_exists:
        JHU_DATA_SOURCE = jhu_data_url(y,m,d,region='US')
        test_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
        r = requests.get(jhu_data_url(y,m,d))
        if r.status_code == 200:
            jhu_csvfile_exists = True
        else:
            if int(d) > 1:
                d -= 1
            elif int(m) > 1:
                m -= 1
                d = 31
            else:
                y -= 1
                m = 12
                d = 31
    latest_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
    df = pd.read_csv(JHU_DATA_SOURCE)
    us_deaths = sum(df['Deaths'])
except:
    us_deaths = None
finally:
    r.close()
# world deaths
try:
    y = time.localtime()[0]
    m = time.localtime()[1]
    d = time.localtime()[2] + 1
    jhu_csvfile_exists = False
    while not jhu_csvfile_exists:
        JHU_DATA_SOURCE = jhu_data_url(y,m,d,region='world')
        test_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
        r = requests.get(jhu_data_url(y,m,d))
        if r.status_code == 200:
            jhu_csvfile_exists = True
        else:
            if int(d) > 1:
                d -= 1
            elif int(m) > 1:
                m -= 1
                d = 31
            else:
                y -= 1
                m = 12
                d = 31
    latest_date = '{:04}'.format(y) + '-' + '{:02}'.format(m) + '-' + '{:02}'.format(d)
    df = pd.read_csv(JHU_DATA_SOURCE)
    world_deaths = sum(df['Deaths'])
except:
    world_deaths = None
finally:
    r.close()
johnshopkins_github = pd.Series([world_deaths, us_deaths], index=['world', 'US'], name='JHU github')


# COVID Tracking Project ------------------------------------------------------
print("pulling from COVID Tracking project...")
# US deaths
try:
    r = requests.get('https://api.covidtracking.com/v1/us/current.json')
    us_deaths = int(float(r.json()[0]['death']))
except:
    us_deaths = None
finally:
    r.close()
# world deaths
try:
    r = requests.get('https://api.covidtracking.com/v1/states/ca/current.json')
    ca_deaths = int(float(r.json()['death']))
except:
    ca_deaths = None
finally:
    r.close()
covidtrackingproject = pd.Series([us_deaths, ca_deaths], index=['US', 'CA'], name='COVID Track Proj')

# CDC -------------------------------------------------------------------------
print("pulling from the CDC...")
# US deaths
try:
    r = requests.get('https://data.cdc.gov/resource/9mfq-cb36.json?$select=max(submission_date)')
    latest_date = r.json()[0]['max_submission_date'][:10]
    us_url = 'https://data.cdc.gov/resource/9mfq-cb36.json?submission_date=' + latest_date + '&$select=sum(tot_death)'
    r_us = requests.get(us_url)
    us_deaths = int(float(r_us.json()[0]['sum_tot_death']))
except:
    us_deaths = None
finally:
    r.close()
    r_us.close()
# CA deaths
try:
    r_ca = requests.get('https://data.cdc.gov/resource/9mfq-cb36.json?state=CA&$select=max(tot_death)')
    ca_deaths = int(float(r_ca.json()[0]['max_tot_death']))
except:
    ca_deaths = None
finally:
    r_ca.close()
cdc = pd.Series([us_deaths, ca_deaths], index=['US', 'CA'], name='CDC')

# WHO -------------------------------------------------------------------------
print("pulling from the WHO...")
try:
    r = requests.get('https://worldhealthorg.shinyapps.io/covid/_w_e3a749be/#tab-8990-1')
    soup = BeautifulSoup(r.text, 'html.parser')
except:
    soup = None
finally:
    r.close()
#  make sure we grabbed the data correctly and don't have an empty list
attempts = 0
try:
    while len(soup.select('span')) == 0:
        print("  ...attempt {0}: got an empty list, trying again...".format(attempts))
        r = requests.get('https://worldhealthorg.shinyapps.io/covid/_w_e3a749be/#tab-8990-1')
        soup = BeautifulSoup(r.text, 'html.parser')
        r.close()
        attempts += 1
        if attempts > 10:
            print("  ...exceeded number of attempts!")
            world_deaths = None
            break
    else:
        world_deaths = int(float(soup.select('span')[25].text.strip()[:-7].replace(' ', '').replace(',', '')))
except:
    world_deaths = None
who = pd.Series([world_deaths], index=['world'], name='WHO')

# LA Times api ----------------------------------------------------------------
print("pulling from the LA Times api...")
# LA deaths
try:
    r = requests.get('https://covid-19.datasettes.com/covid/latimes_county_totals.json?county=Los+Angeles')
    la_deaths = int(float(r.json()['rows'][0][5]))
except:
    la_deaths = None
finally:
    r.close()
# CA deaths
try:
    r = requests.get('https://covid-19.datasettes.com/covid/latimes_state_totals.json')
    ca_deaths = int(float(r.json()['rows'][0][3]))
except:
    ca_deaths = None
finally:
    r.close()
latimes_api = pd.Series([la_deaths, ca_deaths], index=['LA county', 'CA'], name='LAT api')

# LA Times github; pandas
print("pulling from the LA Times github...")
# LA deaths
try:
    URL = 'https://raw.githubusercontent.com/datadesk/california-coronavirus-data/master/latimes-county-totals.csv'
    df = pd.read_csv(URL)
    latest_date = df['date'][0] # date is formatted YYYY-MM-DD
    la_deaths = int(df[(df['county'] == 'Los Angeles') & (df['date'] == latest_date)]['deaths'])
except:
    la_deaths = None
# CA deaths
try:
    ca_deaths = sum(df[df['date'] == latest_date]['deaths'])
except:
    ca_deaths = None
latimes_github = pd.Series([la_deaths, ca_deaths], index=['LA county', 'CA'], name='LAT github')


# CA Dept of Public Health ----------------------------------------------------
print("pulling from California Department of Public Health...")
# CA deaths
try:
    r = requests.get('https://covid19.ca.gov/state-dashboard/')
    soup = BeautifulSoup(r.text, 'html.parser')
    ca_deaths = int(float(soup.find(id='total-deaths-number').text.strip().replace(',', '').replace(' total','')))
except:
    ca_deaths = None
finally:
    r.close()
# LA deaths
try:
    la_url = 'https://data.ca.gov/api/3/action/datastore_search?resource_id=926fd08f-cc91-4828-af38-bd45de97f8c3&sort=date+desc&q=Los+Angeles&limit=1'
    r = requests.get(la_url)
    la_deaths = int(float(r.json()['result']['records'][0]['totalcountdeaths']))
except:
    la_deaths = None
finally:
    r.close()
california = pd.Series([ca_deaths, la_deaths], index=['CA', 'LA county'], name='CDPH')


# save all the data into a table, then transpose it to display sources as rows and death regions as columns
df = pd.concat([
    johnshopkins_github,
    johnshopkins_api,
    latimes_github,
    latimes_api,
    cdc,
    california,
    who,
    covidtrackingproject
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

print('{:7,.0f}'.format(df['United States'].loc['JHU github']), "dead in United States (JHU)")
print('{:7,.0f}'.format(df['LA county'].loc['LAT github']),     "dead in LA county     (LAT)")
print("")

# send data to Adafruit IO ----------------------------------------------------

def send_data(us_cdc, us_jhu, la_cdph, la_lat):
    """send US and LA death data to Adafruit IO dashboard using webhooks"""
    print("sending {0} to us-deaths-cdc feed...".format(us_cdc))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/nAoGyreBPnVSkXzkNF56tC1iH7D7', json={'value': us_cdc})
    print("  data sent!")

    print("sending {0} to us-deaths-jhu feed...".format(us_jhu))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/TJ2LXu6x9Yw8Dz7wr7HisZgHyLLk', json={'value': us_jhu})
    print("  data sent!")

    print("sending {0} to la-deaths-cdph feed...".format(la_cdph))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/FhBcRZCogC43jfRk3BbSs8i1J629', json={'value': la_cdph})
    print("  data sent!")

    print("sending {0} to la-deaths-lat feed...".format(la_lat))
    requests.post('https://io.adafruit.com/api/v2/webhooks/feed/TsvdTi5E1exBefn5SsEUC6fAEayD', json={'value': la_lat})
    print("  data sent!")

send_data(
    us_cdc=int(df['United States'].loc['CDC']),
    us_jhu=int(df['United States'].loc['JHU github']),
    la_cdph=int(df['LA county'].loc['CDPH']),
    la_lat=int(df['LA county'].loc['LAT github'])
    )
