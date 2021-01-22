# covidticker

![fetch latest data and deploy to Adafruit IO](https://github.com/perryrothjohnson/covidticker/workflows/fetch%20latest%20data%20and%20deploy%20to%20Adafruit%20IO/badge.svg)

_How many people have died in the United States and in Los Angeles county?_ Every hour, fetch the data and display it on a wall-mounted LED display ticker--similar to the one shown in [this project](https://learn.adafruit.com/matrix-portal-new-guide-scroller/overview).

A Python script pulls data from the following sources:  
- US deaths
  - [CSSEGISandData/COVID-19](https://github.com/CSSEGISandData/COVID-19) by Johns Hopkins University Center for Systems Science and Engineering  
  - [Centers for Disease Control (CDC)](https://data.cdc.gov/Case-Surveillance/United-States-COVID-19-Cases-and-Deaths-by-State-o/9mfq-cb36)  
- LA County deaths  
  - [datadesk/california-coronavirus-data](https://github.com/datadesk/california-coronavirus-data) by The Los Angeles Times  
  - [California Department of Public Health (CDPH)](https://data.ca.gov/dataset/covid-19-cases/resource/926fd08f-cc91-4828-af38-bd45de97f8c3)

The data is recorded on [Adafruit IO](https://io.adafruit.com/) and is updated hourly using a [scheduled GitHub Action](https://github.com/perryrothjohnson/covidticker/blob/main/.github/workflows/scheduled.yml). Johns Hopkins and LA Times are the primary data sources for US and LA county deaths, respectively. Their figures are typically ahead of the data published by the CDC and CDPH. However, we collect CDC and CDPH data for comparison, and as backups for display on the ticker.

Code written in [CircuitPython](https://circuitpython.org/) runs on an [Adafruit Matrix Portal](https://www.adafruit.com/product/4745) circuit board, powered by [USB-C](https://www.adafruit.com/product/4298). The Matrix Portal uses the [MQTT protocol](https://learn.adafruit.com/mqtt-in-circuitpython/overview) to receive data posted on [Adafruit IO](https://io.adafruit.com/). It is connected to an [RGB LED matrix](https://www.adafruit.com/product/2276), which serves as the LED display ticker.
