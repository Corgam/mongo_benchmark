from math import ceil
from multiprocessing import Process
import multiprocessing
from sqlite3 import Cursor
import time, os, shutil, math, random, gzip, json, pymongo
from datetime import datetime
from csv import DictReader

# Latency checks options
PROCESSES_PER_ITERATION = 1 # How many client processes are added every time step.
WAIT_TIME_PER_ITERATION = 30 # How much time in seconds does the main process wait before latency check. 
UPPER_CLIENT_PROCESSES_LIMIT = 40 # The upper limit of client processes.

# Path and general variables
DATASET_PATH = "/tmp/workload.json.gz"
DATABASE_URL = "mongodb://mongos:27017"
CITIES_PATH = "/tmp/cities_above_1000.csv"
RESULTS_PATH = "/tmp/results.txt"

DATABASE_NAME = "world"
COLLECTION_NAME = "restaurants"
# Radius variables, used for generation of coordinates
SMALLEST_POPULATION = 1000
BIGGEST_POPULATION = 22315474
SMALLEST_POPULATION_RADIUS = 1000
BIGGEST_POPULATION_RADIUS = 44927
SMALLEST_POPULATION_RESTAURANTS = 2
BIGGEST_POPULATION_RESTAURANTS = 100000
# Lists for query generation
RESTAURANT_TYPES = ["Italian", "French", "Japanese", "Polish", "Sushi", "Fastfood", "Home Meals", "Slowfood", "Burgers", "Pizza", "Chinese", "Fushion", "Vegan", "Vegetarian", "Seafood"]
RESTAURANT_NAMES = ["Bar", "Restaurant", "Hotel", "Motel", "Food Truck", "Cafe", "Stand", "Dinner", "Bistro"]
RESTAURANT_PRICES = ["$", "$$", "$$$"]
RESTAURANT_OUTSIDE = [True, False]
# Queries
PROB_END_QUERYING = 0.2 # Probability of ending the query after first response.
PROB_ADDITIONAL_FILTER = 0.6 # Probability of adding additional filtering to basic query.
LATENCY_UPPERBOUND = 0.1 # What is the max. latency. In seconds, where 1 milliseconds = 0.001 seconds
# Global variables
dirName : str = None # The main name of the results folder
procs = [] # List of all currently running processes
finalNumberOfProcesses = 0 # Used for clean-up phase.


class counter_value(object):
    """
    Creates multiprocess safe couter object, which holds an int value.
    The value can be changed or just incremented by one.
    """
    def __init__(self, initialVal = 0) -> None:
        self.val: multiprocessing.Value = multiprocessing.Value("i", initialVal)
        self.lock: multiprocessing.Lock = multiprocessing.Lock()
    def increment(self):
        with self.lock:
            self.val.value += 1
    def set_value(self, new_val):
        with self.lock:
            self.val.value = new_val
    def get_value(self):
        with self.lock:
            return self.val.value


def getCurrentTime():
    """
    Returns a formated, current time.
    """
    return datetime.now().strftime("%d/%m/%Y,%H:%M:%S.%f")


def random_point_in_disk(max_radius):
    """
    Generates a random point in the disk with given radius.
    Source: https://stackoverflow.com/questions/43195899/how-to-generate-random-coordinates-within-a-circle-with-specified-radius
    """
    radius = random.uniform(0,max_radius)
    radians = random.uniform(0, 2*math.pi)
    x = radius * math.cos(radians)
    y = radius * math.sin(radians)
    return [x,y]


def random_location(lon, lat, max_radius):
    """
    Generates a random coordinates pair within a specified circle with given radius and centre coordinate.
    The centre of the circle is given as longitude and latitude pair.
    Source: Source: https://stackoverflow.com/questions/43195899/how-to-generate-random-coordinates-within-a-circle-with-specified-radius
    """
    EarthRadius = 6371
    OneDegree = EarthRadius * 2 * math.pi / 360 * 1000 # 1° latitude in meters
    dx, dy = random_point_in_disk(max_radius)
    random_lat = lat + dy / OneDegree
    random_lon = lon + dx / ( OneDegree * math.cos(lat * math.pi / 180) )
    return[random_lon, random_lat]

    
def calculateRadius(city):
    """
    Calculates a radius for a given city using hardcoded boundary values.
    """
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    return ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)

def addRandomFilterToQuery(query: dict):
    """
    Appends an additional filter to basic quary.
    Filter options: specific cuisine, rating score, pricing or if the restaurant has outside area.
    """
    queryType = random.choice(["restaurantType","ratingScore", "outsideGarden", "cheapPlaces"]) # Choose the type of the query
    if queryType == "restaurantType":
        query["Cuisine"] = { "$eq": random.choice(RESTAURANT_TYPES)}
    elif queryType == "ratingScore":
        query["Rating"] = { "$gt": random.randint(0,4)}
    elif queryType == "outsideGarden":
        query["Outside_area"] = { "$eq": random.choice([True, False])}
    elif queryType == "cheapPlaces":
        query["Pricing"] = { "$eq": random.choice(["$", "$$", "$$$"])}
    return query

def generateBasicQuery(biggest_cities_data: list):
    """
    Generates a query for the database, with the use of random city in the biggest cities dataset.
    """
    meters = random.randint(5000,50000) # Choose the search radius: from 5km to 50km
    random_city = random.choice(biggest_cities_data) # Choose one of the biggest cities
    # Generate random coordinate inside the city's radius
    coordinates = random_location(random_city[0], random_city[1], random_city[2])
    query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } } }
    return query


def preLoad():
    """
    Starts a preload phase, by loading the database with initial workload.
    Logs all preload actions.
    """
    print("Starting preloading...")
    global dirName
    # Create the results file
    timeStr = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    dirName = "Results"+timeStr
    os.makedirs(dirName, exist_ok=True)
    preload = open(dirName+"/preload.txt", "a")
    preload.write("PRELOAD, Start\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedPreload\n")
    # Load the workload
    print("Opening the workload file...")
    with gzip.open(DATASET_PATH, "rb") as fi:
        data = fi.read()
        preload.write(f"{getCurrentTime()},Preload,MainProcess,OpenedWorkloadFile\n")
        print("Decompressing the workload file...")
        decopress = gzip.decompress(data)
        preload.write(f"{getCurrentTime()},Preload,MainProcess,DecompressedTheWorkload\n")
        print("Loading JSON data...")
        restaurants_json = json.loads(decopress)
        preload.write(f"{getCurrentTime()},Preload,MainProcess,LoadedJSONData\n")
    print("Loaded the workload file.")
    # Connect to the mongos
    print("Connecting to MongoDB...")
    client = pymongo.MongoClient(DATABASE_URL, serverSelectionTimeoutMS=1000*500)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    preload.write(f"{getCurrentTime()},Preload,MainProcess,ConnectedToMongo\n")
    # Load the restaurants
    preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedLoadingDataset\n")
    print("Inserting workload to the database. It might take a while...")
    resultInsert = collection.insert_many(restaurants_json, bypass_document_validation=True, ordered=False)
    print(f"Finished inserting workload. Acknowledged: {resultInsert.acknowledged}")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedLoadingDatasetAcknowledged,{resultInsert.acknowledged}\n")
    # Create an geospatial index
    collection.create_index([("location",pymongo.GEOSPHERE)])
    preload.write(f"{getCurrentTime()},Preload,MainProcess,CreatedIndex,2dsphere\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedPreload\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,StartringBenchmarkWithOptions\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,ClientProcessesPerIterationOption,{PROCESSES_PER_ITERATION}\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,WaitTimePerIterationOption,{WAIT_TIME_PER_ITERATION}\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,UpperClientProcessesLimitOption,{UPPER_CLIENT_PROCESSES_LIMIT}\n")
    preload.write("PRELOAD, End\n")
    preload.write("date,time,phase,processName,action,queryID,typeOfQuery,latency\n")
    preload.close()
    print("Finshed preloading.")
    return 1


def startBenchmark():
    """
    Main start of the benchmarking phase. Creates X processes every Y seconds and does latency check-ups. Also,
    keeps track of all created processes, as well as all multiprocess safe values.
    Stops the benchmark, when 2% of latencies exceeded the set value, or if there is at least one timeout.
    """
    print("Starting benchmark...")
    global procs, dirName, finalNumberOfProcesses
    # Start the benchmark logging
    benchmarkFile = open(dirName+"/benchmark.txt", "a")
    benchmarkFile.write(f"{getCurrentTime()},Benchmark,MainProcess,StartedBenchmarking\n")
    benchmarkFile.flush()
    # Create a array of biggest cities
    biggest_cities_data = []
    with open(CITIES_PATH,"r",encoding="utf-8") as dataset:
        dataset_reader = DictReader(dataset, delimiter=';')
        for city in dataset_reader:
            coordinatesString = city['Coordinates'].split(",")
            radius = calculateRadius(city)
            city_data = [float(coordinatesString[1]), float(coordinatesString[0]), radius]
            biggest_cities_data.append(city_data)
    # Create a process safe latency value field
    badLatencies = counter_value(0)
    totalRequests = counter_value(0)
    ifExceptionsArrised = counter_value(0)
    latencyNotexceeded= True
    nextProcessID = 0
    # Parameters
    # Start creating new processes
    while(latencyNotexceeded):
        # Create new processes
        benchmarkFile.write(f"{getCurrentTime()},Benchmark,MainProcess,AddingMoreProcesses,{nextProcessID}\n")
        benchmarkFile.flush()
        for id in range(PROCESSES_PER_ITERATION):
            proc = Process(target=startWorker, args=(nextProcessID, dirName, biggest_cities_data, badLatencies, totalRequests, ifExceptionsArrised ))
            procs.append(proc)
            proc.start()
            nextProcessID += 1
        benchmarkFile.write(f"{getCurrentTime()},Benchmark,MainProcess,CreatedNewProcesses,{nextProcessID}\n")
        benchmarkFile.flush()
        print(f"New {PROCESSES_PER_ITERATION} processes added ({nextProcessID} in total)...")
        # Wait some time
        time.sleep(WAIT_TIME_PER_ITERATION)
        # Check if latency is ok for 98% of the processes
        benchmarkFile.write(f"{getCurrentTime()},Benchmark,MainProcess,LatencyCheck\n")
        benchmarkFile.flush()
        print("Checking the latency in time interval...")
        # Check if maximum throughput was achieved
        if nextProcessID > UPPER_CLIENT_PROCESSES_LIMIT or ifExceptionsArrised.get_value() > 0 or totalRequests.get_value() == 0 or badLatencies.get_value() / totalRequests.get_value() > 0.02:
            print(f"Latency exceeded the upperbound value ({badLatencies.get_value()}/{totalRequests.get_value()}), ending...")
            benchmarkFile.write(f"{getCurrentTime()},Benchmark,MainProcess,LatencyExceeded,{badLatencies.get_value()},{totalRequests.get_value()}\n")
            # Kill all processes
            for proc in procs:
                proc.kill()
            benchmarkFile.flush()
            latencyNotexceeded = False
        else:
            # Clear the previous numbers
            print(f"Latency ok (only {badLatencies.get_value()}/{totalRequests.get_value()}), continuing...")
            benchmarkFile.write(f"{getCurrentTime()},Benchmark,MainProcess,LatencyOk,{badLatencies.get_value()},{totalRequests.get_value()}\n")
            badLatencies.set_value(0)
            totalRequests.set_value(0)
            benchmarkFile.flush()
    benchmarkFile.close()
    # Write the final number of processes
    finalNumberOfProcesses = nextProcessID - 1
    print("Benchmark has ended...")
    return 1


def startWorker(process_id: int, dirName: str , biggest_cities_data: list , numberOfBadLatencies: counter_value, totalRequests: counter_value, ifExceptionsArrised: counter_value):
    """
    Single worker thread which connects to the MongoDB and continously sends queries.
    """
    # TODO: Rework the file opening and closing
    file = open(dirName+f"/worker{process_id}.txt", "a")
    file.write(f"{getCurrentTime()},Benchmark,Process{process_id},Created\n")
    file.flush()
    # Connect to the database
    client = pymongo.MongoClient(DATABASE_URL, serverSelectionTimeoutMS=1000*500)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    # Start sending the queries
    queryID = 0
    while True:
        # Sending the query
        query = generateBasicQuery(biggest_cities_data)
        file.write(f"{getCurrentTime()},Benchmark,Process{process_id},SendingQuery,{queryID}\n")
        file.flush()
        sendTime = datetime.now()
        try:
            response : Cursor = collection.find(query).limit(10)
            responseList = list(response) 
        except Exception as ex:
            responseList = []
            print(f"Connection Timeout: Process{process_id}, {ex}")
            ifExceptionsArrised.increment()
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},Timeout,{queryID}\n")
        latency = datetime.now() - sendTime
        # Log
        file.write(f"{getCurrentTime()},Benchmark,Process{process_id},ReceivedResponse,{queryID},BasicQuery,{latency.microseconds}\n")
        file.flush()
        # Increase total requests count
        totalRequests.increment()
        # Check if wrong latency
        if latency.seconds > LATENCY_UPPERBOUND:
            numberOfBadLatencies.increment()
        # Increase the ID
        queryID += 1  
        # Chance that the query will end
        if_enough_querying = True if random.random() < PROB_END_QUERYING else False
        if if_enough_querying:
            continue    
        # Handle query
        if_additional_filter = True if random.random() < PROB_ADDITIONAL_FILTER else False
        if if_additional_filter:
            # Ask about additional filter
            query = addRandomFilterToQuery(query)
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},SendingQuery,{queryID}\n")
            file.flush()
            # Calculate the latency
            sendTime = datetime.now()
            try:
                response = collection.find(query).limit(10)
                responseList = list(response)
            except Exception as ex:
                responseList = []
                print(f"Connection Timeout: Process{process_id}. {ex}")
                ifExceptionsArrised.increment()
                file.write(f"{getCurrentTime()},Benchmark,Process{process_id},Timeout,{queryID}\n")
            latency = datetime.now() - sendTime
            # Log
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},ReceivedResponse,{queryID},AdditionalFilter,{latency.microseconds}\n")
            file.flush()
            # Increase total requests count
            totalRequests.increment()
            # Check if wrong latency
            if latency.seconds > LATENCY_UPPERBOUND:
                numberOfBadLatencies.increment()
            # Increase the ID
            queryID += 1
        elif len(responseList) == 10:
            # Look into next page
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},SendingQuery,{queryID}\n")
            file.flush()
            # Calculate the latency
            sendTime = datetime.now()
            try:
                response: Cursor = collection.find(query).skip(10).limit(10)
                responseList = list(response)
            except Exception as ex:
                responseList = []
                print(f"Connection Timeout: Process{process_id}. {ex}")
                ifExceptionsArrised.increment()
                file.write(f"{getCurrentTime()},Benchmark,Process{process_id},Timeout,{queryID}\n")
            latency = datetime.now() - sendTime
            # Log 
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},ReceivedResponse,{queryID},NextPage,{latency.microseconds}\n")
            file.flush()
            # Increase total requests count
            totalRequests.increment()
            # Check if wrong latency
            if latency.seconds > LATENCY_UPPERBOUND:
                numberOfBadLatencies.increment()
            # Increase the ID 
            queryID += 1
        
def cleanUp():
    """
    Clean up phase, loads up all seperate results files and copies them into one file.
    """
    print("Cleaning up...")
    # Prepare the list of files
    fileNames = [dirName+"/preload.txt", dirName+"/benchmark.txt"]
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
    """
    The main pipeline of the benchmark.
    """
    # Init the seed
    random.seed(2022)
    # Start the preload 
    if (preLoad() != 1):
        print("ERROR: PreLoading did not go well!")
    # Start the experiment
    if (startBenchmark() != 1):
        print("ERROR: Benchmarking did not go well!")
    # Clean-up the benchmark
    if (cleanUp() != 1):
        print("ERROR: Cleanup did not go well!")