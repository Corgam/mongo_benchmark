from pymongo import MongoClient

client = MongoClient('mongodb://imongo:27017')

db = client["ini"]
collection = db['col']
document = {"name": "Corgam", "source": "stackoverflow", "question": 70157757}
collection.insert_one(document)