# MongoDB Benchmark

This is a repository containing a MongoDB Database Benchmark. The goal of the Benchmark is to compare the maximum througputs for MongoDB Databases containing geospatial data. Three architectures of MongoDB databases will be compared: without sharding, with 2 shards, and with 3 shards. 

**Research question:** benchmark aims to check if the maximum load for last two of the mentioned scenarios will be doubled and trippeled respectively, compared to the database without shards. 

# Setup

### 1. Setting up MongoDB

1. Type your credentials for Google Cloud Platform in the config file (used by Terraform to create VMs).
2. Run `make setup-mongo N=SHARDS_NUMBER` command in order to create MongoDB's VMs on GCP, with `N` equal to the number of shards the Mongo database will have (either `1`,`2` or `3`). For example: `make setup-mongo N=2` will setup Mongo database with 2 shards.
3. Wait until the VMs are ready.
4. Run the benchmark.

### 2. Running the benchmark

1. Run `make benchmark` command to create a Benchmarking Client VM on GCP.
2. After VM is ready, the benchmark will start immediately.
3. Wait until the end of the benchmark (the progress can be seen in the terminal).


### 3. Collecting results and analysis

1. Run `make clean` to destroy all VMs on GCP.
2. Open the results file.
