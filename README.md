# Cisco 9800 WLC monitoring dashboard
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/grafana/images/full_dashboard.png)

This repository consists of:

- NETCONF collector - Python project, collects useful wireless metrics from Cisco 9800 WLC
- DNAC collector - Python project, collects useful wireless metrics from DNAC
- Grafana Dashboard - Visualise metrics received from collector app(s)

Grafana and InfluxDB are required, please follow installation instructions on grafana.com and influxdata.com respectively.

**Wireless metrics (collected using NETCONF)**

- Connected clients
- Client states
- Client types
- Client count
- WLC LAN Throughput
- AP metrics
  - channel Utilization
  - client count
  - site-tag
  - rf-tag
  - channel changes

**Wireless metrics (collected from DNAC)**
- WNCD process utilization


## NETCONF collector

Makes NETCONF calls to 9800 WLC, parses output, sends to Influx DB, saves to CSV

Edit config.ini to configure options

Configure the following environment variables:
- WLC_USER
- WLC_PASS
- INFLUX_API_KEY

NETCONF collector can be run directly
```
python3 netconf-collector.py
```
or as a Docker container
```
git clone https://github.com/Johnny8Bit/wifi-dashboard
cd wifi-dashboard
docker build -t netcollector -f netconf/Dockerfile .
docker run -d --name netcollector --network host --mount type=bind,source="$(pwd)"/logs,destination=/netconf/logs netcollector
```
The **--mount** parameter is optional and used to map CSV output folder to Docker host, CSV save option can be enabled in config.ini

## DNAC collector

Makes API calls to DNAC, parses output, sends to InfluxDB

Edit config.ini to configure options

Configure the following environment variables:
- DNAC_USER
- DNAC_PASS
- INFLUX_API_KEY

DNAC collector can be run directly
```
python3 dnac-collector.py
```
or as a Docker container
```
git clone https://github.com/Johnny8Bit/wifi-dashboard
cd wifi-dashboard
docker build -t dnacollector -f dnac/Dockerfile .
docker run -d --name dnacollector --network host dnacollector
```
## Grafana Dashboard

Grafana dashboard .json export is available in /grafana folder, import into existing Grafana installation

The InfluxDB datasource uid will need to be modified 

Sample screenshots:

![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/grafana/images/client_metrics.png)
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/grafana/images/throughput_and_wncd.png)

## Project status

This is a work in progress, some items may not work in your network deployment

Tested on Catalyst 9800 running 17.9.3 code at scale (~11,000 clients)

Tested on Raspberry Pi

