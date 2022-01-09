from multiprocessing import Process
import time, os, toml, shutil
import pymongo
from datetime import datetime
from csv import DictReader

CONFIG_PATH = "/tmp/config.toml"
RESULTS_PATH = "/tmp/results.txt"
DATASET_PATH = "/tmp/dataset.csv"
DATABASE_NAME = "worship"
COLLECTION_NAME = "places"

# Global variables
dirName : str = None
procs = []
finalNumberOfProcesses = 0


def getCurrentTime():
    return datetime.now().strftime("%d/%m/%Y,%H:%M:%S.%f")


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
    header.write("date,time,phase,processName,action,queryID,ifAcknowledged,insertedID\n")
    header.close()
    return 1
    

def preLoad():
    print("Starting preloading...")
    preload = open(dirName+"/preload.txt", "a")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedPreload\n")
    # Connect to the mongos
    client = pymongo.MongoClient("mongodb://mongos:27017")
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    preload.write(f"{getCurrentTime()},Preload,MainProcess,ConnectedToMongo\n")
    # Start loading the dataset
    with open(DATASET_PATH,"r", encoding="utf-8-sig") as dataset:
        dataset_reader = DictReader(dataset)
        # Read every row
        preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedLoadingDataset\n")
        loadingStatus = 0
        for row in dataset_reader:
            # Prepare for insertion
            location = {"location":{"type":"Point", "coordinates":[float(row['X']),float(row['Y'])]}}
            row.pop("X")
            row.pop("Y")
            row.update(location)
            # Insert
            collection.insert_one(row)
            # Log from time to time
            loadingStatus += 1
            if loadingStatus % 5000 == 0:
                print(f"Loaded {loadingStatus} observations...")
                preload.write(f"{getCurrentTime()},Preload,MainProcess,LoadedObservations,{loadingStatus}\n")
    # Create an geospatial index
    collection.create_index([("location",pymongo.GEOSPHERE)])
    preload.write(f"{getCurrentTime()},Preload,MainProcess,CreatedIndex,2dsphere\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedLoadingDataset\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedPreload\n")
    preload.close()
    print("Finshed preloading...")
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
    # Join all proceses
    time.sleep(60)
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
    client = pymongo.MongoClient("mongodb://mongos:27017")
    db = client["testDatabase"]
    collection = db["testCollection"]
    # Start sending the queries
    return
    i = 0
    while True:
        # Sending the query
        file = open(dirName+f"/worker{id}.txt", "a")
        file.write(f"{getCurrentTime()},Benchmark,Process{id},SendingQuery,{i}\n")
        file.close()
        print(f"Process{id}: Sending query{i}...")
        document = {"processID": id, "queryID" : i, "name": "Corgam"}
        response = collection.insert_one(document)
        # Receiving the response
        file = open(dirName+f"/worker{id}.txt", "a")
        file.write(f"{getCurrentTime()},Benchmark,Process{id},ReceivedResponse,{i},{response.acknowledged},{response.inserted_id}\n")
        file.close()
        i += 1
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
    with open(RESULTS_PATH, "wb") as finalFile:
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

if __name__ == '__main__':
    # Open the config
    with open(CONFIG_PATH) as f:
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