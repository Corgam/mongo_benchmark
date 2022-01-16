from math import ceil
from multiprocessing import Process
import time, os, toml, shutil, math, random
import pymongo
from datetime import datetime
from csv import DictReader
from matplotlib import pyplot as plt

# Path variables
CONFIG_PATH = "/tmp/config.toml"
RESULTS_PATH = "/tmp/results.txt"
DATASET_PATH = "/tmp/cities_above_1000.csv"
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
    

def addRestaurants_with_plot(city, collection):
    # Calculate radius
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    radius = ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)
    # Calculate number of restaurants
    restaurants_no = ceil((population_proc * (BIGGEST_POPULATION_RESTAURANTS - SMALLEST_POPULATION_RESTAURANTS)) + SMALLEST_POPULATION_RESTAURANTS)
    # Create restaurants
    x = []
    y = []
    coordinates = city["location"]["coordinates"]
    for i in range(restaurants_no):
        location = random_location(coordinates[0], coordinates[1], radius)
        restaurant = createRestaurantJSON(location, city["Name"])
        x.append(location[0])
        y.append(location[1])
        #collection.insert_one(restaurant)
    plt.scatter(coordinates[0],coordinates[1], color = "red")
    plt.scatter(x,y)
    plt.show()
    plt.close()


def createRestaurantJSON(location, city):
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
    restaurant.update({"location":{"type":"Point", "coordinates":[float(location[0]), float(location[1])]}})
    return restaurant
    

def addRestaurants(city, collection):
    # Calculate radius
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    radius = ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)
    # Calculate number of restaurants
    restaurants_no = ceil((population_proc * (BIGGEST_POPULATION_RESTAURANTS - SMALLEST_POPULATION_RESTAURANTS)) + SMALLEST_POPULATION_RESTAURANTS)
    # Create restaurants
    coordinates = city["location"]["coordinates"]
    for i in range(restaurants_no):
        location = random_location(coordinates[0], coordinates[1], radius)
        restaurant = createRestaurantJSON(location, city["Name"])
        collection.insert_one(restaurant)
    return restaurants_no



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
            location = {"location":{"type":"Point", "coordinates":[float(coordinates[0]), float(coordinates[1])]}}
            row.pop("Coordinates")
            row.update(location)
            # Insert
            collection.insert_one(row)
            # Add the restaurants
            restaurants_added += addRestaurants(row, collection)
            # Log from time to time
            loadingStatus += 1
            if loadingStatus % 5000 == 0:
                print(f"Loaded {loadingStatus} cities (with {restaurants_added} restaurants)...")
                preload.write(f"{getCurrentTime()},Preload,MainProcess,LoadedObservations,{loadingStatus}\n")
    print(f"Added in total {restaurants_added} restaurants the the database.")
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