# Cisco Catalyst 9800 monitoring dashboard

This repository consists of:

- NETCONF collector - Python project, collects useful wireless metrics from Cisco 9800 using NETCONF
- RADKIT collector - Python project, collects useful wireless metrics from Cisco 9800 using SSH (via RADKit)
- Grafana dashboards - Pretty graphs

The following components are used, see respective sites for installation instructions.
- Grafana - grafana.com
- InfluxDB 2.x - influxdata.com
- MySQL - mysql.com
- RADKit - radkit.cisco.com
- (Optional) Docker - docker.com

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

This dashboard code was used at Cisco Live Amsterdam 2025 / 2026.

However, it is not officially supported by Cisco, and may not work in your environment.

There is no regression testing on this project, and YANG models evolve over time; i.e. things that were fixed or added for newer IOS-XE versions no longer work on older versions.

Last tested at scale (>15K clients) on IOS-XE 17.18.2 

## Notes

For IOS-XE versions before 17.9.5 - CSCwf78066 _may_ be a concern

Python 3.10+ required

Developed and tested on Ubuntu

## Grafana Dashboard

Grafana dashboard .json exports are available in **grafana/** directory, import into existing Grafana installation

Queries can be modified to show data from different Controller/SSID names, or to filter AP metrics by RF/Site tag

The InfluxDB datasource UID will need to be modified

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
- INFLUX_ORG
- INFLUX_HOST
- INFLUX_BUCKET
- INFLUX_API_KEY

RADKit collector can be run directly or in a Docker container

There may be differences in the setup & operation of RADKit client between RADKit versions, if in doubt check the RADKit release notes.

Last verified RADKit version is: 2.0.12

Flow diagram
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/images/ssh-flow.png)

## Docker

Docker is an optional component.

The collector scripts for NETCONF and SSH can be deployed as Docker containers.

The benefit is that containers can be run in detached mode (in the background) and set to auto-restart in the event of a script problem, there is no other functional difference.

Influx / Grafana / MySQL / RADKit can also be deployed as Docker containers if so required, however, installing these as native services is preferred.

## License

This software is licensed under the Cisco Sample Code License

URL: https://developer.cisco.com/docs/licenses/cisco-sample-code-license/
