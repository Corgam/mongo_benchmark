# Run the mongo container
docker run --name mongodb -p 27017:27017 -d mongo:5.0.4
# Copy the files to the container
docker cp /tmp/configserver.conf mongodb:/configserver.conf
docker cp /tmp/init.js mongodb:/init.js
# Create empty dirs to copy them
mkdir customdata
mkdir logging
# Create empty dirs inside of the container
docker cp ./customdata mongodb:/customdata
docker cp ./logging mongodb:/logging
docker exec mongodb /bin/sh -c "mongod --config configserver.conf --fork --logpath /logging/configserver.log"
docker exec mongodb /bin/sh -c "mongosh --norc localhost:27019 ./init.js"
