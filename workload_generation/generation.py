import gzip
import json
from math import ceil
import math, random
from csv import DictReader

DATASET_PATH = "workload_generation/cities_above_1000.csv"
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

# Prepare
# Delete the line below in order to generate new workloads.
# The seed is here, for repetition of the results, when repo is cloned on different machine.
random.seed(2020) 
restaurants_data = []

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
    restaurant.update({"Name":f"{type} {name} {random.randint(1,1000)}"})
    restaurant.update({"City":city})
    restaurant.update({"Cuisine": type})
    restaurant.update({"Opened": random.randint(1970,2022)})
    restaurant.update({"Rating": random.randint(1,5)})
    restaurant.update({"Reviews": random.randint(1,1000)})
    restaurant.update({"Pricing": random.choice(RESTAURANT_PRICES)})
    restaurant.update({"Outside_area": random.choice(RESTAURANT_OUTSIDE)})
    restaurant.update({"location":{"type":"Point", "coordinates":[float(long), float(lat)]}})
    return restaurant
    
def calculateRadius(city):
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    return ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)

def calculateRestaurantNo(city):
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    return ceil((population_proc * (BIGGEST_POPULATION_RESTAURANTS - SMALLEST_POPULATION_RESTAURANTS)) + SMALLEST_POPULATION_RESTAURANTS)
   

def addRestaurants(city):
    # Calculate radius
    radius = calculateRadius(city)
    # Calculate number of restaurants
    restaurants_no = calculateRestaurantNo(city)
    # Create restaurants
    coord = city["location"]["coordinates"]
    for i in range(restaurants_no):
        long, lat = random_location(coord[0], coord[1], radius)
        restaurant = createRestaurantJSON(long, lat, city["Name"])
        # Add restaurant
        restaurants_data.append(restaurant)

# Generate the restaurants
print("Started generating the workload...")
with open(DATASET_PATH,"r",encoding="utf-8") as dataset:
    dataset_reader = DictReader(dataset, delimiter=';')
    # Read every row
    loadingStatus = 0
    for row in dataset_reader:
        # Prepare coordinates
        coordinates = row['Coordinates'].split(",")
        # Inside the dataset, long and lat are switched, so lat is first, long second. We need to switch them arround.
        location = {"location":{"type":"Point", "coordinates":[float(coordinates[1]), float(coordinates[0])]}} 
        row.pop("Coordinates")
        row.update(location)
        # Add the restaurants
        addRestaurants(row)
        loadingStatus = loadingStatus +1
        # Uncomment the lines below to generate restaurants for smaller number of cities (smaller size of workload file).
        # if loadingStatus == 5000:
        #     break
        if loadingStatus % 10000 == 0:
            print(f"Genereted restaurants for {loadingStatus} cities.")


# Save the workload file
print("Started compressing the data...")
restaurants_json = json.dumps(restaurants_data)
encoded = restaurants_json.encode("utf-8")
compressed = gzip.compress(encoded)
print("Started writing data to a file...")
with gzip.open("workload_generation/workload.json.gz", "wb") as f:
    f.write(compressed)
