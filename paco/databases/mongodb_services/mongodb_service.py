import os
import sys

from pymongo import MongoClient, errors

conn = None


def init_database():
    try:
        global conn
        conn = MongoClient(
            host=os.environ.get('MONGODB_DOMAIN'),
            port=os.environ.get('MONGODB_PORT'),
            username=os.environ.get('MONGO_ROOT_USER'),
            password=os.environ.get('MONGO_ROOT_PASSWORD'),
        )
        print("Debug: Database connection established")
        print("MondoDB-Server version:", conn.server_info()["version"])
        # database_names = conn.list_database_names()
        # print("\ndatabases:", database_names)

        return True
    except errors.PyMongoError as e:
        print(f"Error connecting to MongoDB Platform: {e}")
        sys.exit(1)


def upsert(id, graph_dictionary):
    graph_database = conn["graph-database"]
    mongo_collection = graph_database["graph-collection"]
    mongo_collection.replace_one({"_id": id}, graph_dictionary, upsert=True)
    print(f"Upsert {id} to Database")
