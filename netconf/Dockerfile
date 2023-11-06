FROM ubuntu:jammy
RUN apt update
RUN apt -y install python3
RUN apt -y install pip
WORKDIR /netconf/logs
WORKDIR /netconf
COPY ../netconf-collector.py .
COPY ../config.ini .
COPY ../requirements.txt .
COPY ../libs/*.py libs/
RUN pip install -r requirements.txt
ENV WLC_USER=username
ENV WLC_PASS=password
ENV INFLUX_API_KEY=influxapikey
CMD ["netconf-collector.py"]
ENTRYPOINT ["python3", "-u"]
