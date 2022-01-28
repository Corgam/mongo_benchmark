from math import ceil
from multiprocessing import Process
from sqlite3 import Cursor
import time, os, shutil, math, random, gzip, json, pymongo
from datetime import datetime
from csv import DictReader

# Debug
DATASET_PATH = "workload_generation/workload.json.gz"
DATABASE_URL = "mongodb://localhost:27017"
# Path variables
RESULTS_PATH = "/tmp/results.txt"
#DATASET_PATH = "/tmp/workload.json.gz"
DATABASE_NAME = "world"
COLLECTION_NAME = "restaurants"
#DATABASE_URL = "mongodb://mongos:27017"
# Radius variables
SMALLEST_POPULATION = 1000
BIGGEST_POPULATION = 22315474
SMALLEST_POPULATION_RADIUS = 1000
BIGGEST_POPULATION_RADIUS = 44927
SMALLEST_POPULATION_RESTAURANTS = 2
BIGGEST_POPULATION_RESTAURANTS = 100000
# Lists
RESTAURANT_TYPES = ["Italian", "French", "Japanese", "Polish", "Sushi", "Fastfood", "Home Meals", "Slowfood", "Burgers", "Pizza", "Chinese", "Fushion", "Vegan", "Vegetarian", "Seafood"]
RESTAURANT_NAMES = ["Bar", "Restaurant", "Hotel", "Motel", "Food Truck", "Cafe", "Stand", "Dinner", "Bistro"]
RESTAURANT_PRICES = ["$", "$$", "$$$"]
RESTAURANT_OUTSIDE = [True, False]
# Query probabilities
PROB_END_QUERYING = 0.2
PROB_ADDITIONAL_FILTER = 0.6

# Global variables
dirName : str = None
procs = []
finalNumberOfProcesses = 0


def getCurrentTime():
    return datetime.now().strftime("%d/%m/%Y,%H:%M:%S.%f")


def initLogging():
    print("Starting logging...")
    global results_file, dirName
    # Create the results file
    timeStr = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
    dirName = "Results"+timeStr
    # dirName = "Results"+ str(config["benchmark_run_id"]) +"_Shards"+ str(config["number_of_mongo_shards"]) +"_"+timeStr
    os.makedirs(dirName, exist_ok=True)
    header = open(dirName+"/header.txt", "a")
    # Add header
    header.write("HEADER, Start\n")
    #header.write("Benchmark id, "+ str(config["benchmark_run_id"]) +"\n")
    #header.write("Number of MongoDB shards, "+ str(config["number_of_mongo_shards"]) +"\n")
    header.write("Time of benchmark, "+ timeStr+"\n")
    header.close()
    return 1
    

def random_point_in_disk(max_radius):
    # Source: https://stackoverflow.com/questions/43195899/how-to-generate-random-coordinates-within-a-circle-with-specified-radius
    radius = random.uniform(0,max_radius)
    radians = random.uniform(0, 2*math.pi)
    x = radius * math.cos(radians)
    y = radius * math.sin(radians)
    return [x,y]


def random_location(lon, lat, max_radius):
    # Source: https://stackoverflow.com/questions/43195899/how-to-generate-random-coordinates-within-a-circle-with-specified-radius
    EarthRadius = 6371
    OneDegree = EarthRadius * 2 * math.pi / 360 * 1000 # 1° latitude in meters
    dx, dy = random_point_in_disk(max_radius)
    random_lat = lat + dy / OneDegree
    random_lon = lon + dx / ( OneDegree * math.cos(lat * math.pi / 180) )
    return[random_lon, random_lat]

    
def calculateRadius(city):
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    return ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)

def addRandomFilterToQuery(query: dict):
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
    Generates a query for the database.
    """
    meters = random.randint(5000,50000) # Choose the search radius: from 5km to 50km
    random_city = random.choice(biggest_cities_data) # Choose one of the biggest cities
    # Generate random coordinate inside the city's radius
    coordinates = random_location(random_city[0], random_city[1], random_city[2])
    query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } } }
    return query


def preLoad():
    print("Starting preloading...")
    preload = open(dirName+"/preload.txt", "a")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedPreload\n")
    # Load the workload
    print("Opening the workload file...")
    with gzip.open("workload_generation/workload.json.gz", "rb") as fi:
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
    client = pymongo.MongoClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    preload.write(f"{getCurrentTime()},Preload,MainProcess,ConnectedToMongo\n")
    # Load the restaurants
    preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedLoadingDataset\n")
    print("Inserting workload to the database. It might take a while...")
    collection.insert_many(restaurants_json)
    print("Finished inserting workload.")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedLoadingDataset\n")
    # Create an geospatial index
    collection.create_index([("location",pymongo.GEOSPHERE)])
    preload.write(f"{getCurrentTime()},Preload,MainProcess,CreatedIndex,2dsphere\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedPreload\n")
    preload.write("HEADER, End\n")
    preload.write("date,time,phase,processName,action,queryID,ifAcknowledged,numberOfResults,insertedID\n")
    preload.close()
    print("Finshed preloading...")
    return 1


def startBenchmark():
    print("Starting benchmark...")
    global procs, dirName, finalNumberOfProcesses
    # Create a array of biggest cities
    biggest_cities_data = []
    with open(DATASET_PATH,"r",encoding="utf-8") as dataset:
        dataset_reader = DictReader(dataset, delimiter=';')
        for city in dataset_reader:
            coordinatesString = city['Coordinates'].split(",")
            radius = calculateRadius(city)
            city_data = [float(coordinatesString[1]), float(coordinatesString[0]), radius]
            biggest_cities_data.append(city_data)
    # Creating new processes
    for id in range(100):
        proc = Process(target=startWorker, args=(id, dirName, biggest_cities_data, ))
        procs.append(proc)
        proc.start()
        time.sleep(5)
    # Join all proceses
    time.sleep(60)
    finalNumberOfProcesses = len(procs)
    for proc in procs:
        proc.kill()
    print("Benchmark has ended...")
    return 1


def startWorker(process_id : int, dirName: str, biggest_cities_data: list):
    """
    Single worker thread which connects to the MongoDB and continously sends queries.
    """
    # TODO: Rework the file opening and closing
    file = open(dirName+f"/worker{process_id}.txt", "a")
    file.write(f"{getCurrentTime()},Benchmark,Process{process_id},Created\n")
    file.flush()
    # Connect to the database
    client = pymongo.MongoClient(DATABASE_URL)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    # Start sending the queries
    queryID = 0
    while True:
        # Sending the query
        query = generateBasicQuery(biggest_cities_data)
        file.write(f"{getCurrentTime()},Benchmark,Process{process_id},SendingQuery,{queryID}\n")
        file.flush()
        #print(f"Process{process_id}: Sending query{queryID}...\n")
        response : Cursor = collection.find(query).limit(10)
        responseList = list(response)
        file.write(f"{getCurrentTime()},Benchmark,Process{process_id},ReceivedResponseBatch,{queryID},ACK?!,-\n")
        file.flush()
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
            #print(f"Process{process_id}: Sending query{queryID}...\n")
            response = collection.find(query).limit(10)
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},ReceivedResponseBatch,{queryID},ACK?!,-\n")
            file.flush()
            queryID += 1
        elif len(responseList) == 10:
            # Look into next page
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},SendingQuery,{queryID}\n")
            file.flush()
            #print(f"Process{process_id}: Sending query{queryID}...\n")
            response: Cursor = collection.find(query).skip(10).limit(10)
            file.write(f"{getCurrentTime()},Benchmark,Process{process_id},ReceivedResponseBatch,{queryID},ACK?!,-\n")
            file.flush()
            queryID += 1
        
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
    # Init the seed
    random.seed(2022)
    # Init the logging
    if (initLogging() != 1):
        print("ERROR")
    # Start the preload 
    if (preLoad() != 1):
        print("ERROR")
    # Start the experiment
    if (startBenchmark() != 1):
        print("ERROR")
    # Clean-up the benchmark
    if (cleanUp() != 1):
        print("ERROR")