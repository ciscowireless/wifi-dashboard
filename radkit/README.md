To run the RADKit collector in a Docker container:
```
git clone https://github.com/ciscowireless/wifi-dashboard
cd wifi-dashboard/radkit
```
- Download RADKit from https://radkit.cisco.com/downloads/release/
- For Linux, place the downloaded .tgz file in the same directory as the Dockerfile
- Edit the Dockerfile > update the RADKit installation package filename to the version you are using
- This project was build using RADKit 1.7.0
```
docker build -t radkit-collector .
docker run -d --network host radkit-collector
```