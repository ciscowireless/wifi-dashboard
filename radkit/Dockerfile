FROM python:3.12.7-slim-bullseye
ENV TZ=Europe/Warsaw
ENV INFLUX_ORG=influx_org
ENV INFLUX_BUCKET=influx_bucket
ENV INFLUX_API_KEY=influx_api_key
ENV RADKIT_USER=radkit_admin_username
ENV RADKIT_PASS=radkit_admin_password
RUN apt update
RUN python3 -m pip install -U pip
RUN pip install --upgrade pip
WORKDIR /radkit/wheels
COPY cisco_radkit_1.7.0_pip_linux_x86.tgz .
RUN tar zxvf cisco_radkit_1.7.0_pip_linux_x86.tgz
RUN python3 -m pip install -f . cisco_radkit_client
WORKDIR /radkit
COPY wncd-radkit.py .
CMD ["wncd-radkit.py"]
ENTRYPOINT ["python3", "-u"]
HEALTHCHECK NONE