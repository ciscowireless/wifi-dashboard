## Updated dashboards will be posted here after Cisco Live Amsterdam 2025 

# Cisco 9800 WLC monitoring dashboard

This repository consists of:

- NETCONF collector - Python project, collects useful wireless metrics from Cisco 9800 using NETCONF
- RADKIT collector - Python project, collects useful wireless metrics from Cisco 9800 using SSH (via RADKit)
- Grafana Dashboard - Makes pretty graphs

The following components are used, see respective sites for installation instructions.
- Grafana - grafana.com
- InfluxDB 2.x - influxdata.com
- MySQL - mysql.com
- RADKit - radkit.cisco.com
- (Optional) Docker - www.docker.com

**Wireless metrics (collected via NETCONF)**

- Connected clients
- Client states
- Client types
- Client count
- WLC LAN Throughput
- WLC Inventory (HW/SW)
- WLC SSO state
- AP metrics
  - channel Utilization
  - client count
  - site-tag
  - rf-tag
  - model

**Wireless metrics (collected via SSH/RADKit)**
- WNCD process utilization

## Project status

This is a work in progress, some items may not work in your network deployment

Tested on Catalyst 9800 running 17.9, 17.12, and 17.15, and at scale (>10K clients)

For IOS-XE versions before 17.9.5 - CSCwf78066 _may_ be a concern

Python 3.10+, not tested on Windows

## Grafana Dashboard

Grafana dashboard .json export is available in **grafana/** directory, import into existing Grafana installation

Queries can be easily modified to show data from different WLC/SSID names, or to filter AP metrics by RF/Site tag

The InfluxDB datasource UID will need to be modified

Sample screenshots:

![Image](https://github.com/ciscowireless/wifi-dashboard/blob/main/images/client-capabilities.png)
![Image](https://github.com/ciscowireless/wifi-dashboard/blob/main/images/client-summary.png)
![Image](https://github.com/ciscowireless/wifi-dashboard/blob/main/images/radios-channel-utilization.png)
![Image](https://github.com/ciscowireless/wifi-dashboard/blob/main/images/radios-client-count.png)
![Image](https://github.com/ciscowireless/wifi-dashboard/blob/main/images/wlc-summary.png)
![Image](https://github.com/ciscowireless/wifi-dashboard/blob/main/images/dashboard-statistics.jpg)

## NETCONF collector

Makes NETCONF calls directly to devices, parses output, stores temporary data in MySQL, sends to InfluxDB

Edit **config.json** to configure options

Configure the following environment variables:
- MYSQL_USER
- MYSQL_PASS
- INFLUX_API_KEY
- IOSXE_USER (configurable per-device via config.json)
- IOSXE_USER (configurable per-device via config.json)

NETCONF collector can be run directly or in a Docker container

Flow diagram
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/images/netconf-flow.png)

## MySQL

- Create an admin user with privileges to write/delete data
- Create new database and update database name in **config.json**
- Commands to create the required tables are in the **mysql/** directory

MySQL is used for _temporary_ data manipulation only

## RADKIT collector

Makes API calls using RADKit Client API, parses output, sends to InfluxDB

RADKit is currently used only for WNCD load metrics colected via SSH

Configure the following environment variables:
- RADKIT_USER
- RADKIT_PASS
- INFLUX_API_KEY
- INFLUX_ORG
- INFLUX_BUCKET

RADKit collector can be run directly or in a Docker container

Depending on RADKIt version, it may be neccesary to downgrade the __httpx__ library
```
pip install httpx=0.27.2
```
Flow diagram
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/images/ssh-flow.png)

## Docker

Docker is an optional component.

The collector scripts for NETCONF and SSH can be deployed as Docker containers.

The benefit is that contaners can be run in detached mode (in the background) and set to auto-restart in the event of a script problem, there is no other functional difference.

Influx / Grafana / MySQL / RADKit can also be depoyed as Docker contaners if so required, however, installing these as native services is preferred.

## License

This software is licensed under the Cisco Sample Code License

URL: https://developer.cisco.com/docs/licenses/cisco-sample-code-license/



