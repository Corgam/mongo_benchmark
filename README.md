# MongoDB Benchmark

This is a repository containing a MongoDB Database Benchmark. The goal of the Benchmark is to compare the maximum througputs for MongoDB Databases containing geospatial data. Three architectures of MongoDB databases will be compared: without sharding, with 2 shards, and with 3 shards. 

**Research question:** benchmark aims to check if the maximum load for last two of the mentioned scenarios will be doubled and trippeled respectively, compared to the database without shards. 

# Setup

### 1. Requirements

1. Setup a default Ubuntu X.XX VM inside the Compute Engine on the GCP.
2. Download the Git (`sudo apt-get install git`) and clone this repository (`sudo git clone https://github.com/Corgam/mongo_benchmark`).
3. Run the `make setup` to install all necessary applications.
4. Change the config file to your liking.
5. Upload the JSON file containing the credentials to your gcp account as specified in the config 

### 2. Setting up MongoDB

1. Type your credentials for Google Cloud Platform in the config file (used by Terraform to create VMs).
2. Run `make mongo n=SHARDS_NUMBER` command in order to create MongoDB's VMs on GCP, with `n` equal to the number of shards the Mongo database will have (either `1`,`2` or `3`). For example: `make mongo n=2` will setup Mongo database with 2 shards.
3. Wait until the VMs are ready.

### 3. Running the benchmark

Before running the benchmark, make sure that all Mongo's VMs are ready to be used and connected to.

1. Run `make benchmark` command to create a Benchmarking Client VM on GCP.
2. After VM is ready, the benchmark will start immediately.
3. Wait until the end of the benchmark (the progress can be seen in the terminal).


### 4. Collecting results and analysis

1. Connect with `SSH` to the benchmarking client's VM.
2. Go to `/home/ubuntu` and save the results file (named: `Results*_Shards*_TIME.txt`).
3. Run `make clean` to destroy all VMs on GCP.