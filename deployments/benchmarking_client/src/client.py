from pymongo import MongoClient
from multiprocessing import Process
import time, os, toml, shutil
from datetime import datetime

CONFIG_PATH = "/tmp/config.toml"

# Global variables
dirName : str = None
procs = []
finalNumberOfProcesses = 0

def initLogging(config):
    print("Starting logging..")
    global results_file, dirName
    # Create the results file
    timeStr = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    dirName = "Results"+ str(config["benchmark_run_id"]) +"_Shards"+ str(config["number_of_mongo_shards"]) +"_"+timeStr
    os.makedirs(dirName, exist_ok=True)
    header = open(dirName+"/header.txt", "a")
    # Add header
    header.write("HEADER, Start\n")
    header.write("Benchmark id, "+ str(config["benchmark_run_id"]) +"\n")
    header.write("Number of MongoDB shards, "+ str(config["number_of_mongo_shards"]) +"\n")
    header.write("Time of benchmark, "+ timeStr+"\n")
    header.write("HEADER, End\n")
    header.write("date,time,phase,processName,action\n")
    header.close()
    return 1
    

def preLoad():
    print("Preloading...")
    preload = open(dirName+"/preload.txt", "a")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,Started\n")
    client = MongoClient('mongodb://imongo:27017')
    preload.write(f"{getCurrentTime()},Preload,MainProcess,Finished\n")
    preload.close()
    return 1

def warmUp():
    return 1



def startBenchmark(config):
    print("Starting benchmark...")
    global procs, dirName, finalNumberOfProcesses
    # Creating new processes
    for id in range(3):
        proc = Process(target=startWorker, args=(id, dirName, ))
        procs.append(proc)
        proc.start()
        time.sleep(config["new_process_interval"])
    #db = client["ini"]
    #collection = db['col']
    #document = {"name": "Corgam", "source": "stackoverflow", "question": 70157757}
    #collection.insert_one(document)

    # Join all proceses
    finalNumberOfProcesses = len(procs)
    for proc in procs:
        proc.kill()
    print("Benchmark has ended...")
    return 1


def startWorker(id : int, dirName: str):
    """
    Single worker thread which connects to the MongoDB and continously sends queries.
    """
    # TODO: Rework the file opening and closing
    file = open(dirName+f"/worker{id}.txt", "a")
    file.write(f"{getCurrentTime()},Benchmark,Process{id},Created\n")
    file.close()
    # Connect to the database
    #client = MongoClient('mongodb://imongo:27017')
    # Start sending the queries
    while True:
        file = open(dirName+f"/worker{id}.txt", "a")
        file.write(f"{getCurrentTime()},Benchmark,Process{id},SendingQuery\n")
        file.close()
        time.sleep(1)
    # Close the file

def cleanUp():
    print("Cleaning up...")
    # Prepare the list of files
    # TODO: When copying sort by the time
    fileNames = [dirName+"/header.txt", dirName+"/preload.txt"]
    for i in range(finalNumberOfProcesses):
        fileNames.append(dirName+f"/worker{i}.txt")
    # Create the final result file
    with open(dirName+".txt", "wb") as finalFile:
        for f in fileNames:
            with open(f, 'rb') as fd:
                shutil.copyfileobj(fd,finalFile)
    # Delete the temp folder
    try:
        shutil.rmtree(dirName)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))
    # Close the file
    return 1

def getCurrentTime():
    return datetime.now().strftime("%d/%m/%Y,%H:%M:%S")


if __name__ == '__main__':
    # Open the config
    with open("./config.toml") as f:
        config = toml.load(f)
    # Init the logging
    if (initLogging(config) != 1):
        print("ERROR")
    # Start the preload 
    if (preLoad() != 1):
        print("ERROR")
    # Start the warm-up
    if (warmUp() != 1):
        print("ERROR")
    # Start the experiment
    if (startBenchmark(config) != 1):
        print("ERROR")
    # Clean-up the benchmark
    if (cleanUp() != 1):
        print("ERROR")