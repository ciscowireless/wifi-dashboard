FROM python:3.12.7-slim-bullseye
ENV TZ=Europe/Warsaw
ENV INFLUX_HOST=localhost
ENV INFLUX_PORT=8086
ENV INFLUX_ORG=
ENV INFLUX_BUCKET=
ENV INFLUX_API_KEY=
ENV RADKIT_USER=
ENV RADKIT_PASS=
ENV RADKIT_HOST=localhost
RUN apt update
RUN python3 -m pip install -U pip
RUN pip install --upgrade pip
WORKDIR /radkit/wheels
COPY cisco_radkit_1.8.1_pip_linux_x86.tgz .
RUN tar zxvf cisco_radkit_1.8.1_pip_linux_x86.tgz
RUN python3 -m pip install -f . cisco_radkit_client
WORKDIR /radkit
COPY wncd-radkit.py .
CMD ["wncd-radkit.py"]
ENTRYPOINT ["python3", "-u"]
HEALTHCHECK NONE
