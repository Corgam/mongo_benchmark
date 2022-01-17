from math import ceil
from multiprocessing import Process
import time, os, toml, shutil, math, random
import pymongo
from datetime import datetime
from csv import DictReader
from matplotlib import pyplot as plt

# Path variables
#CONFIG_PATH = "/tmp/config.toml"
CONFIG_PATH = "config.toml"
RESULTS_PATH = "/tmp/results.txt"
#DATASET_PATH = "/tmp/cities_above_1000.csv"
DATASET_PATH = "deployments/benchmarking_client/data/cities_above_1000.csv"
DATABASE_NAME = "worship"
COLLECTION_NAME = "places"
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


def createRestaurantJSON(long, lat, city):
    restaurant = {}
    type = random.choice(RESTAURANT_TYPES)
    name = random.choice(RESTAURANT_NAMES)
    restaurant.update({"name":f"{type} {name} {random.randint(1,1000)}"})
    restaurant.update({"city":city})
    restaurant.update({"cuisine": type})
    restaurant.update({"opened": random.randint(1970,2022)})
    restaurant.update({"rating": random.randint(1,5)})
    restaurant.update({"reviews": random.randint(1,1000)})
    restaurant.update({"pricing": random.choice(RESTAURANT_PRICES)})
    restaurant.update({"outside_area": random.choice(RESTAURANT_OUTSIDE)})
    restaurant.update({"location":{"type":"Point", "coordinates":[float(long), float(lat)]}})
    return restaurant
    

def addRestaurants(city, collection):
    # Calculate radius
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    radius = ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)
    # Calculate number of restaurants
    restaurants_no = 2#ceil((population_proc * (BIGGEST_POPULATION_RESTAURANTS - SMALLEST_POPULATION_RESTAURANTS)) + SMALLEST_POPULATION_RESTAURANTS)
    # Create restaurants
    coord = city["location"]["coordinates"]
    for i in range(restaurants_no):
        long, lat = random_location(coord[0], coord[1], radius)
        restaurant = createRestaurantJSON(long, lat, city["Name"])
        collection.insert_one(restaurant)
    return restaurants_no


def generateQuery(biggest_cities_coords: list):
    """
    """
    meters = random.randint(5000,50000) # Choose the search radius: from 5km to 50km
    # TODO: Choose points between cities
    coordinates = random.choice(biggest_cities_coords) # Choose one of the biggest cities
    queryType = random.choice(["radiusSearch","restaurantType","ratingScore", "outsideGarden", "cheapPlaces"]) # Choose the type of the query
    if queryType == "radiusSearch":
        query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } } }
    elif queryType == "restaurantType":
        query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } }, "cuisine": { "$eq": random.choice(RESTAURANT_TYPES)}  }
    elif queryType == "ratingScore":
        query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } }, "rating": { "$gt": random.randint(0,4)}  }
    elif queryType == "outsideGarden":
        query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } }, "outside_area": { "$eq": random.choice([True, False])}  }
    elif queryType == "cheapPlaces":
        query = { "location": { "$nearSphere": { "$geometry": { "type": "Point", "coordinates": coordinates }, "$maxDistance": meters } }, "pricing": { "$eq": random.choice(["$", "$$", "$$$"])}  }
    return query


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
    restaurants_added = 0
    with open(DATASET_PATH,"r",encoding="utf-8") as dataset:
        dataset_reader = DictReader(dataset, delimiter=';')
        # Read every row
        preload.write(f"{getCurrentTime()},Preload,MainProcess,StartedLoadingDataset\n")
        loadingStatus = 0
        for row in dataset_reader:
            # Prepare coordinates
            coordinates = row['Coordinates'].split(",")
             # Inside the dataset, long and lat are switched, so lat is first, long second. We need to switch them arround.
            location = {"location":{"type":"Point", "coordinates":[float(coordinates[1]), float(coordinates[0])]}} 
            row.pop("Coordinates")
            row.update(location)
            # Insert
            #collection.insert_one(row)
            # Add the restaurants
            #restaurants_added += addRestaurants(row, collection)
            # Log from time to time
            loadingStatus += 1
            if loadingStatus % 5000 == 0:
                print(f"Loaded {loadingStatus} cities (with {restaurants_added} restaurants)...")
                preload.write(f"{getCurrentTime()},Preload,MainProcess,LoadedObservations,{loadingStatus}\n")
    print(f"Added in total {restaurants_added} restaurants the the database.")
    # Create an geospatial index
    #collection.create_index([("location",pymongo.GEOSPHERE)])
    preload.write(f"{getCurrentTime()},Preload,MainProcess,CreatedIndex,2dsphere\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedLoadingDataset\n")
    preload.write(f"{getCurrentTime()},Preload,MainProcess,FinishedPreload\n")
    preload.close()
    print("Finshed preloading...")
    return 1


def startBenchmark(config):
    print("Starting benchmark...")
    global procs, dirName, finalNumberOfProcesses
    # Create a array of biggest cities
    biggest_cities_coords = []
    with open(DATASET_PATH,"r",encoding="utf-8") as dataset:
        dataset_reader = DictReader(dataset, delimiter=';')
        for row in dataset_reader:
            coordinatesString = row['Coordinates'].split(",")
            coordinates = [float(coordinatesString[1]), float(coordinatesString[0])]
            biggest_cities_coords.append(coordinates)
    # Creating new processes
    for id in range(3):
        proc = Process(target=startWorker, args=(id, dirName, biggest_cities_coords, ))
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


def startWorker(id : int, dirName: str, biggest_cities_coords: list):
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
    i = 0
    while True:
        # Sending the query
        file = open(dirName+f"/worker{id}.txt", "a")
        file.write(f"{getCurrentTime()},Benchmark,Process{id},SendingQuery,{i}\n")
        file.close()
        print(f"Process{id}: Sending query{i}...")
        query = generateQuery(biggest_cities_coords)
        response = collection.find(query)
        # Receiving the response
        file = open(dirName+f"/worker{id}.txt", "a")
        file.write(f"{getCurrentTime()},Benchmark,Process{id},ReceivedResponse,{i},{response.acknowledged},{response.inserted_id}\n")
        file.close()
        i += 1
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
    # Start the experiment
    if (startBenchmark(config) != 1):
        print("ERROR")
    # Clean-up the benchmark
    if (cleanUp() != 1):
        print("ERROR")