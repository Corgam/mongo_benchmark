# MongoDB Benchmark

This is a repository containing a MongoDB Database Benchmark, done for Cloud Service Benchmarking [WiSe2122] course at TU Berlin. The goal of the Benchmark is to answer the following research question:

***RQ 1: How does the maximum throughput change while scaling out the MongoDB database containing geospatial workload?***


In more detail, we compare the maximum throughputs for MongoDB Databases containing geospatial data. Three scenarios and thus architectures of MongoDB databases will be compared: without sharding, with 2 shards, and with 3 shards. 

More about the benchmark itself, SUT and background information, exact implementation details and results analysis can be read in the Benchmark Report (soon to come!).

## Implementation
When a benchmark is run, with the use of Terraform, firstly all necessary VMs for the database itself will be deployed on GCP, then benchmarking client will be also deployed on its own VM. The database will be preloaded with the previously generated geospatial workload, and from the start of the benchmark, queried with generated "on the go", geospatial queries. 

Every 30 seconds, 5 new client processes will be created on the benchmarking client, thus simulating the increase of the database reads. Additionally, after every 30 seconds, the latency will be checked for all sent requests during that period. If the latency is exceeded for 2% of the requests, or timeout happens the benchmark will end.

Results file containing the logs made throughout the whole benchmark will be sent back to the host VM executing the benchmark. The results can be analyzed using the Jupyter Notebooks in the `data_analysis` folder.

Exact details on how to execute the benchmark yourself can be found below in the `Execution` section.

## Results

The results of the Benchmark, including all plots can be seen in the Benchmark Report (soon to come!).
The plots based on the results can be also seen in the `figures` folder.

# Execution

### 1. Requirements and setup

1. Log into your GCP account and create a new project called `mongodb-benchmark`. Use this project for further instructions.
2. Setup a host VM inside the Compute Engine and SSH into it. (Tested with an e2-standard-8 VM with default Ubuntu 20.04 LTS, no guarantees are given for other types of VMs (some might have problem with the lack of resources to generate the workload) or the OS) If the host VM stops generating the workload, it requires more RAM.
3. Download all necessary packages: run `sudo apt-get update` and then `sudo apt-get install git make`. 
4. Clone this repository (`sudo git clone https://github.com/Corgam/mongo_benchmark`).
5. Create the GCP's JSON credentials file (Follow: https://cloud.google.com/iam/docs/creating-managing-service-account-keys) and save it as `credentials.json` in the root folder of the repository. (where this `README.md` and `Makefile` are)
6. Inside of the repo's root folder, run the `sudo make setup` to create the required SSH keys, generate the workload and download all necessary Python packages.
(The workload size can be changed in the `workload_generation/generation.py` file. Change the `BIGGEST_POPULATION_RESTAURANTS` global constant, to change the possible maximum amount of restaurants per city)

### 2. Setting up MongoDB

1. Run `make mongo n=SHARDS_NUMBER` command to create MongoDB's VMs on GCP, with `n` equal to the number of shards the Mongo database will have (either `1`, `2` or `3`). For example: `make mongo n=2` will set up Mongo database with 2 shards.
2. Wait until the VMs are ready.

### 3. Running the benchmark

Before running the benchmark, make sure that all Mongo's VMs are ready to be used and connected to.

1. Run the `make benchmark` command to create a Benchmarking Client VM on GCP.
2. After VM is ready, the benchmark will start immediately.
3. Wait until the end of the benchmark (the progress can be seen in the terminal).

### 4. Collecting results, cleanup, and analysis

1. The results file should be located in the root directory of this repository. (named: `Results_[TIME].txt`).
2. Run `make clean` to destroy all VMs on GCP.
3. To analyze the results, one can use the Jupyter Notebooks located in the `data_analysis` folder.
