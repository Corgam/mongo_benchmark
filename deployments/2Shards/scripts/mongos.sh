#! /bin/bash
# Download docker
sudo apt-get update
sudo apt-get --assume-yes install ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get --assume-yes install docker-ce docker-ce-cli containerd.io
# Run the MongoDB container
sudo docker run --name mongodb -p 27017:27017 -d mongo:5.0.4
until [ "`sudo docker inspect -f {{.State.Running}} mongodb`"=="true" ]; do
    sleep 0.1;
done;
# Copy all necessary files to the container
sudo mkdir customdata
sudo mkdir logging
sudo docker cp /tmp/mongos.conf mongodb:/mongos.conf
sudo docker cp /tmp/initiate.js mongodb:/initiate.js
sudo docker cp ./customdata mongodb:/customdata
sudo docker cp ./logging mongodb:/logging
# # Run the config server
#sudo docker exec mongodb /bin/sh -c "mongod --config mongos.conf --fork --logpath /logging/mongos.log"
#sudo docker exec mongodb /bin/sh -c "mongosh --norc localhost:27018 ./initiate.js"
