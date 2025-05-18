# Step-by-Step manual build

## Operating system

Ubuntu Desktop 22.04 (recommended)

## git

Install
```
sudo apt install git -y
```
Clone Wi-Fi Dashboard repository
```
git clone https://github.com/ciscowireless/wifi-dashboard
```

## pip

Install
```
sudo apt install python3-pip -y
```
Install required libraries
```
cd wifi-dashboard
pip install -r requirements.txt
```

## Docker (Optional)

Install Docker Engine: https://docs.docker.com/engine/install/ubuntu/

Docker Engine post-install
```
sudo groupadd docker
sudo usermod -aG docker your_linux_user
newgrp docker
```

## MySQL

Install
```
sudo apt install mysql-server -y
```
Configure
```
sudo mysql
CREATE USER 'mysql_user'@'localhost' IDENTIFIED BY 'mysql_password';
GRANT ALL PRIVILEGES ON *.* TO 'mysql_user'@'localhost';
exit
mysql -u mysql_user -p
CREATE DATABASE database_name;
USE database_name;
```
Create new tables by copying statements from **wifi-dashboard/mysql/table-create.txt**

## InfluxDB

Install InfluxDB: https://www.influxdata.com/downloads

Do <ins>not</ins> use: https://docs.influxdata.com/influxdb/v2/install/

Launch: http://localhost:8086

Create:
- Admin user
- Organization
- Bucket

Save:
- API token

## Grafana

Install Grafana: https://grafana.com/docs/grafana/latest/setup-grafana/installation/debian/

Start Grafana: https://grafana.com/docs/grafana/latest/setup-grafana/start-restart-grafana/

Launch: http://localhost:3000
- Default credentials: admin/admin
- Change password

Navigate:
- Home > Connections > Add new connection > InfluxDB
- Add new data source

| Parameter | Value |
| --- | --- |
| Query language | InfluxQL |
| URL | http://localhost:8086 |
| Custom HTTP Headers |
| Header | Authorization |
| Value | Token <influx_api_token> |
| Database | Influx bucket |

- Save & test

Navigate:
- Home > Dashboard
- New > Import
- Upload dashboard JSON file

Import all files in **wifi-dashboard/grafana** one by one

For each panel in each dashboard:
- Edit
- Datasource > Re-Select InfluxDB (default)
- Save dashboard

The imported dashboards may have reference to other device IP addresess and/or other AP models, these need to be updated to reflect the devices in your environment.
This is easily done in the Grafana UI after the .json files are imported.

## Wi-Fi Dashboard - NETCONF

Edit: **wifi-dashborad/config.json**

Update “general” section with values from previous steps:
- mysql_db
- influx_org 
- influx_bucket

Update “wlc” section with device details, for each monitored device:
- name
- ip
- WLC LAN interface
- username environment variable name
- password environment variable name

Create environment variables
```
sudo nano /etc/environment
```
| Environment variable | Value |
| --- | --- |
| IOSXE_USER (configurable in previous step) | netconf_username |
| IOSXE_PASS (configurable in previous step)| netconf_password |
| MYSQL_USER | mysql_user |
| MYSQL_PASS | mysql_password |
| INFLUX_API_KEY | influx_api_token |

Run:
```
python3 dashboard.py
```

## (Docker) Wi-Fi Dashboard - NETCONF

Edit: **wifi-dashborad/Dockerfile**

Update environment variables

| Environment variable | Value |
| --- | ---|
| ENV IOSXE_USER | netconf_username |
| ENV IOSXE_PASS | netconf_password |
| ENV MYSQL_USER | mysql_user |
| ENV MYSQL_PASS | mysql_password |
| ENV INFLUX_API_KEY | influx_api_token |

Build
```
cd wifi-dashboard
docker build -t netconf-collector .
```
Run
```
docker run -d –name netconf-collector –network host –restart always netconf-collector
```
Verify
```
docker attach –sig-proxy=false netconf-collector
```

## IOS-XE device configuration

Credentials for NETCONF and should be privilege 15

Configure
```
aaa authorization exec default local
```

## RADKit Service (system wide)

Install RADKit Service: https://radkit.cisco.com/docs/install/install_linux_systemd.html

Bootstrap RADKit Service: https://radkit.cisco.com/docs/install/install_linux.html#install-linux-bootstrap

Navigate: https://localhost:8081

For each monitored device:

Devices > Add new Device
- Device name
- Device Type (IOS-XE)
- IP or hostname
- Available Management Protocols = Terminal
- SSH username
- SSH password
- Enable Password (if required)

Create RADKit Admin user:

Admin Users > Add Admin
- Admin Name
- Password
- Confirm Password

## RADKit Client (pip)

Download RADKit pip installation: **cisco_radkit_1.7.x_pip_linux.tgz**

```
mkdir radkit-pip-install
cd radkit-pip-install
tar zxvf cisco_radkit_1.7.x_pip_linux.tgz
python3 -m pip install -f . cisco_radkit_client
```
Update version number as needed

## Wi-Fi Dashboard – SSH

Create environment variables
```
sudo nano /etc/environment
```
| Environment variable | Value |
| --- | ---|
| RADKIT_USER | radkit_admin_username |
| RADKIT_PASS | radkit_admin_password |
| INFLUX_API_KEY | influx_api_token |
| INFLUX_ORG | influx_org |
| INFLUX_BUCKET | influx_bucket |

Run
```
python3 wncd-radkit.py
```

## (Docker) Wi-Fi Dashboard – SSH

Copy to same directory as Dockerfile: **cisco_radkit_1.7.x_pip_linux.tgz**

Edit: **wifi-dashborad/radkit/Dockerfile**

Update environment variables
```
ENV RADKIT_USER=radkit_admin_username
ENV RADKIT_PASS=radkit_admin_password
ENV INFLUX_API_KEY=influx_api_token
ENV INFLUX_ORG=influx_org
ENV INFLUX_BUCKET=influx_bucket
```
Update (as needed)
```
COPY cisco_radkit_1.7.x_pip_linux_x86.tgz .
RUN tar zxvf cisco_radkit_1.7.x_pip_linux_x86.tgz
```
Build
```
docker build -t radkit-collector .
```
Run
```
docker run -d –-name radkit-collector –-network host –restart always radkit-collector
```
Verify
```
docker attach –sig-proxy=false radkit-collector
```
