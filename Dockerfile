FROM python:3.12.7-slim-bullseye
ENV TZ=Europe/Warsaw
ENV INFLUX_API_KEY=
ENV MYSQL_USER=
ENV MYSQL_PASS=
ENV IOSXE_USER=
ENV IOSXE_PASS=
RUN apt update
RUN python3 -m pip install -U pip
RUN pip install mysql-connector-python
RUN pip install ncclient
RUN pip install requests
WORKDIR /dashboard/libs
COPY libs/influx.py .
COPY libs/mysql.py .
COPY libs/netconf.py .
WORKDIR /dashboard
COPY config.json .
COPY dashboard.py .
CMD ["dashboard.py"]
ENTRYPOINT ["python3", "-u"]
HEALTHCHECK NONE