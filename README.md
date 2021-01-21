# covidticker

![fetch latest data and deploy to Adafruit IO](https://github.com/perryrothjohnson/covidticker/workflows/fetch%20latest%20data%20and%20deploy%20to%20Adafruit%20IO/badge.svg)

A wall-mounted ticker, which updates daily with the total number of COVID-19 deaths for the United States and Los Angeles county.

This project uses a Python script to pull data from [Johns Hopkins](https://github.com/CSSEGISandData/COVID-19), [LA Times](https://github.com/datadesk/california-coronavirus-data), the [CDC](https://data.cdc.gov/Case-Surveillance/United-States-COVID-19-Cases-and-Deaths-by-State-o/9mfq-cb36), and [CDPH](https://data.ca.gov/dataset/covid-19-cases/resource/926fd08f-cc91-4828-af38-bd45de97f8c3). It runs periodically and records the data on [Adafruit IO](https://io.adafruit.com/). Johns Hopkins and LA Times are the primary data sources for US and LA county deaths, respectively. The CDC and CDPH are secondary data sources, and can be used as alternates for display.

Code written in [CircuitPython](https://circuitpython.org/) runs on an [Adafruit Matrix Portal](https://www.adafruit.com/product/4745) circuit board, powered by [USB-C](https://www.adafruit.com/product/4298). The Matrix Portal uses the [MQTT protocol](https://learn.adafruit.com/mqtt-in-circuitpython/overview) to receive data from [Adafruit IO](https://io.adafruit.com/). It is connected to an [RGB LED matrix](https://www.adafruit.com/product/2276), which serves as the ticker display.
