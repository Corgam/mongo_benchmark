# #! /bin/bash
# Install MongoDB
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv B00A0BD1E2C63C11
echo "deb [arch=amd64] http://repo.mongodb.org/apt/ubuntu $(lsb_release -sc)/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org.list
sudo apt update
sudo apt --assume-yes install mongodb-org
# Make necessary directories
sudo mkdir /tmp/database
sudo mkdir /tmp/logging
# Run the mongos
sudo mongos --config /tmp/mongos.conf --fork --logpath /tmp/logging/mongos.log
sudo mongosh --norc localhost:27017 /tmp/mongos.js
