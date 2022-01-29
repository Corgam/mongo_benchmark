# MongoDB Benchmark

This is a repository containing a MongoDB Database Benchmark. The goal of the Benchmark is to compare the maximum througputs for MongoDB Databases containing geospatial data. Three architectures of MongoDB databases will be compared: without sharding, with 2 shards, and with 3 shards. 

**Research question:** benchmark aims to check if the maximum load for last two of the mentioned scenarios will be doubled and trippeled respectively, compared to the database without shards. 

# Setup

### 1. Requirements and setup

1. Log into your GCP account and create a new project called `mongodb-benchmark`. Use this project for further instructions.
2. Setup a default Ubuntu X.XX VM inside the Compute Engine and SSH into it.
3. Download the Git (`sudo apt-get install git`) and clone this repository (`sudo git clone https://github.com/Corgam/mongo_benchmark`).
4. Create the GCP's JSON credentials file (Follow: https://cloud.google.com/iam/docs/creating-managing-service-account-keys) and save it as `credentials.json` in the root folder of the repository. (where this `README.md` and `Makefile` are)
5. Run the `make setup` to install all necessary applications, the create SSH keys and generate the workload.
(The workload size can be changed in the `workload_generation/generation.py` file. Change the `BIGGEST_POPULATION_RESTAURANTS` global constant, to change the possible maximum amount of restaurants per city)

### 2. Setting up MongoDB

1. Run `make mongo n=SHARDS_NUMBER` command in order to create MongoDB's VMs on GCP, with `n` equal to the number of shards the Mongo database will have (either `1`,`2` or `3`). For example: `make mongo n=2` will setup Mongo database with 2 shards.
2. Wait until the VMs are ready.

### 3. Running the benchmark

Before running the benchmark, make sure that all Mongo's VMs are ready to be used and connected to.

1. Run `make benchmark` command to create a Benchmarking Client VM on GCP.
2. After VM is ready, the benchmark will start immediately.
3. Wait until the end of the benchmark (the progress can be seen in the terminal).

### 4. Collecting results, cleanup and analysis

1. The results file should be located in the root directory of this repository. (named: `Results_[TIME].txt`).
2. Run `make clean` to destroy all VMs on GCP.
3. In order to analyze the results, one can use the Jupyter Notebooks located in the `data_analysis` folder.
