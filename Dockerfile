FROM python:3.12.7-slim-bullseye
ENV TZ=Europe/Warsaw
ENV INFLUX_API_KEY=api-key
ENV MYSQL_USER=username
ENV MYSQL_PASS=password
ENV IOSXE_USER=username
ENV IOSXE_PASS=password
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