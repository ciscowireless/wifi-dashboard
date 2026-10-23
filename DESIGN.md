## System Design

### NETCONF flow diagram
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/images/netconf-flow.png)

### SSH flow diagram
![Image](https://github.com/Johnny8Bit/wifi-dashboard/blob/main/images/ssh-flow.png)

### Splunk

The same code can be used to feed Splunk dashboards, just point the output to Splunk instead of Influx.
Or, send output to Telegraf and feed both Grafana and Splunk simultaneously.
Splunk configuration is out of scope here.
