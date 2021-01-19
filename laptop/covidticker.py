import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd

# global flags
print_inline = False
print_table = True

# Johns Hopkins
if print_inline:
    print("\nJohns Hopkins:")
else:
    print("\npulling from Johns Hopkins...")
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

# # Johns Hopkins unofficial API
# if print_inline:
#     print("\nJohns Hopkins:")
# else:
#     print("\npulling from Johns Hopkins...")
# api_response = requests.get('https://covid19api.herokuapp.com/deaths')
# world_deaths = int(float(api_response.json()['latest']))
# if print_inline:
#     print("World deaths:", world_deaths)
# # look up the index for United States in the JSON list (it should be 247?)
# r = api_response.json()
# dict_of_country_codes = {}
# for i in np.arange(len(r['locations'])):
#     code = r['locations'][i]['country_code']
#     dict_of_country_codes[code] = i
#     # print (code, i)
# us_deaths = int(float(r['locations'][dict_of_country_codes['US']]['latest']))
# if print_inline:
#     print("US deaths:", us_deaths)
# johnshopkins = pd.Series([world_deaths, us_deaths], index=['world', 'US'], name='Johns Hopkins')

# Johns Hopkins API (alternate)
# docs: https://documenter.getpostman.com/view/10808728/SzS8rjbc
# main page: https://covid19api.com/


# COVID Tracking Project
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

# CDC
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

# WHO
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

# LA Times
if print_inline:
    print("\nLA Times:")
else:
    print("pulling from the LA Times...")
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
print(' ',latest_date)
la_deaths = int(df[(df['county'] == 'Los Angeles') & (df['date'] == latest_date)]['deaths'])
if print_inline:
    print("LA County deaths:", la_deaths)
latimes_github_pandas = pd.Series([la_deaths], index=['LA county'], name='LA Times github-pandas')

# LA Times github; requests
if print_inline:
    print("\nLA Times github-requests")
else:
    print("pulling from the LA Times github with requests...")
api_response = requests.get('https://raw.githubusercontent.com/datadesk/california-coronavirus-data/master/latimes-county-totals.csv')
t = api_response.text
latest_date_rt = t.split('\n')[1].split(',')[0]
county_row = 19
county = t.split('\n')[county_row].split(',')[1]
if print_inline:
    print(' ',latest_date_rt)
    print(' ',county)
if county == 'Los Angeles':
    la_deaths = int(t.split('\n')[county_row].split(',')[4])
else:
    error_msg = "expecting data for Los Angeles, but instead got data for " + county
    raise Exception(error_msg)
if print_inline:
    print("LA County deaths:", la_deaths)
latimes_github_requests = pd.Series([la_deaths], index=['LA county'], name='LA Times github-requests')

# Johns Hopkins github; pandas
if print_inline:
    print("\nJohns Hopkins github-pandas:")
else:
    print("pulling from Johns Hopkins github with pandas...")
year = latest_date[:4]
month = latest_date[5:7]
day = latest_date[8:]
latest_date_JHU = month + '-' + day + '-' + year
if print_inline:
    print(' ',latest_date_JHU)
URL = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/' + latest_date_JHU + '.csv'
df = pd.read_csv(URL)
us_deaths = sum(df['Deaths'])
if print_inline:
    print("US deaths:", us_deaths)
johnshopkins_github_pandas = pd.Series([us_deaths], index=['US'], name='Johns Hopkins github-pandas')

# Johns Hopkins github; requests
if print_inline:
    print("\nJohns Hopkins github-requests:")
else:
    print("pulling from Johns Hopkins github with requests...")
year = latest_date[:4]
month = latest_date[5:7]
day = latest_date[8:]
latest_date_JHU = month + '-' + day + '-' + year
if print_inline:
    print(' ',latest_date_JHU)
api_response = requests.get('https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_daily_reports_us/' + latest_date_JHU + '.csv')
t = api_response.text
# state death totals are in column 6
# ignore the column headers in row 0
# ignore the blank line in the last row (row -1)
us_deaths = 0
for state in t.split('\n')[1:-1]:
    state_deaths = int(state.split(',')[6])
    us_deaths += state_deaths
if print_inline:
    print("US deaths:", us_deaths)
johnshopkins_github_requests = pd.Series([us_deaths], index=['US'], name='Johns Hopkins github-requests')

# CA Dept of Public Health
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
    johnshopkins, 
    johnshopkins_github_pandas, 
    johnshopkins_github_requests,
    who, 
    cdc, 
    california, 
    covidtrackingproject, 
    latimes, 
    latimes_github_pandas,
    latimes_github_requests,
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
    if df['United States'].loc['Johns Hopkins github-requests'] > 1.1*(df['United States'].loc['CDC']):
        print('{:7,.0f}'.format(df['United States'].loc['CDC']),  "dead in United States (CDC)")
    else:
        print('{:7,.0f}'.format(df['United States'].loc['Johns Hopkins github-requests']),  "dead in United States (JHU)")
except:
    print('{:7,.0f}'.format(df['United States'].loc['CDC']),  "dead in United States (CDC)")

# check for errors in LA county data ... if LA Times data is > 10% off from CDPH data, display CDPH instead
try:
    if df['LA county'].loc['LA Times github-requests'] > 1.1*(df['LA county'].loc['CDPH']):
        print('{:7,.0f}'.format(df['LA county'].loc['CDPH']),     "dead in LA county     (CDPH)")
    else:
        print('{:7,.0f}'.format(df['LA county'].loc['LA Times github-requests']),     "dead in LA county     (LAT)")
except:
    print('{:7,.0f}'.format(df['LA county'].loc['CDPH']),     "dead in LA county     (CDPH)")
print("")
