import subprocess, os
from datetime import datetime

# Load the ip of the client
with open("deployments/benchmarking_client/clientIP.txt","r") as file:
    client_ip = file.readline()
# Copy the results file from the client
timeStr = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
dirName = "Results_" + timeStr
subprocess.call(f"scp -o StrictHostKeyChecking=no -i deployments/benchmarking_client/clientkey ubuntu@{client_ip}:/tmp/results.txt {dirName}.txt", shell=True)
# Clean up
os.remove("deployments/benchmarking_client/clientIP.txt")