from posixpath import dirname
import shutil
import os
from datetime import datetime
import subprocess

from pyrsistent import b

# Prepare the name and the header
with open("header.txt", "a") as header:
    header.truncate(0)
    header.write("HEADER, Start\n")
    timeStr = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    header.write("TimeOfBenchmark, "+ timeStr+"\n")
    with open("number_of_shards_in_last_run.txt", "r", encoding="utf-8") as f:
        number_of_shards = f.read()
        header.write("NumberOfShards,"+number_of_shards+"\n")
    # If first benchmark, write new file
    if not os.path.exists("id_of_last_run_benchmark.txt"):
        with open("id_of_last_run_benchmark.txt", "w") as f:
            f.write("0")
            benchmark_id = 0
    else:
        with open("id_of_last_run_benchmark.txt", "r") as f:
            benchmark_id = int(f.read())
            if benchmark_id == 0:
                benchmark_id = 1
        with open("id_of_last_run_benchmark.txt", "w") as fi:
            new_value = benchmark_id + 1
            fi.truncate(0)
            fi.write(f"{new_value}")
    header.write(f"BenchmarkID,{benchmark_id}\n")
    header.write("HEADER, End\n")
# Load the ip of the client
with open("deployments/benchmarking_client/clientIP.txt","r") as file:
    client_ip = file.readline()
# Copy the results file from the client
timeStr = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
subprocess.call(f"scp -o StrictHostKeyChecking=no -i deployments/benchmarking_client/clientkey ubuntu@{client_ip}:/tmp/results.txt results.txt", shell=True)
# Clean up
os.remove("deployments/benchmarking_client/clientIP.txt")
# Append header
fileNames = ["header.txt", "results.txt"]
# Create the final result file
dirName = f"Results{benchmark_id}_Shards{number_of_shards}_" + timeStr
with open(f"{dirName}.txt", "wb") as finalFile:
    for f in fileNames:
        with open(f, 'rb') as fd:
            shutil.copyfileobj(fd,finalFile)
# Delete the temp folder
try:
    os.remove("results.txt")
    os.remove("header.txt")
except OSError as e:
    print("Error: %s - %s." % (e.filename, e.strerror))