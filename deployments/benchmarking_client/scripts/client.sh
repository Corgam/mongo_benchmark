#! /bin/bash
# Install requirements
sudo apt-get update
sudo apt-get --assume-yes install python3-pip
python3 -m pip install -r /tmp/requirements.txt
# Run the benchmarking client
python3 /tmp/client.py