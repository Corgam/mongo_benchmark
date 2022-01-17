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

def addRestaurants_with_plot(city, collection):
    # Calculate radius
    population = int(city["Population"]) if int(city["Population"]) != 0 else 1000
    population_proc = ((population - SMALLEST_POPULATION)) / (BIGGEST_POPULATION - SMALLEST_POPULATION)
    radius = ceil((population_proc * (BIGGEST_POPULATION_RADIUS - SMALLEST_POPULATION_RADIUS)) + SMALLEST_POPULATION_RADIUS)
    # Calculate number of restaurants
    restaurants_no = 2#ceil((population_proc * (BIGGEST_POPULATION_RESTAURANTS - SMALLEST_POPULATION_RESTAURANTS)) + SMALLEST_POPULATION_RESTAURANTS)
    # Create restaurants
    x = []
    y = []
    coordinates = city["location"]["coordinates"] # Inside the dataset, long and lat are switched, so lat is first, long second.
    for i in range(restaurants_no):
        long, lat = random_location(coordinates[0], coordinates[1], radius) # Switch around the lat and long
        restaurant = createRestaurantJSON(long, lat, city["Name"])
        x.append(long)
        y.append(lat)
    plt.scatter(coordinates[1],coordinates[0], color = "red")
    plt.scatter(x,y)
    plt.show()
    plt.close()
    return restaurants_no