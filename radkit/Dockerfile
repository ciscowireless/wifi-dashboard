FROM python:3.12.7-slim-bullseye
ENV TZ=Europe/Warsaw
ENV INFLUX_API_KEY=api-key
ENV RADKIT_USER=username
ENV RADKIT_PASS=password
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