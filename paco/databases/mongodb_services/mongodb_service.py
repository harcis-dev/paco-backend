import os
import sys

from pymongo import MongoClient, errors

from paco.utils import configs as ct, utils

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
        print("MongoDB: Database connection established")
        return True
    except errors.PyMongoError as e:
        print(f"Error connecting to MongoDB Platform: {e}")
        sys.exit(1)


init_database()  # Connect to MongoDB


def upsert_graphs(set_id, graph_dictionary):
    global conn
    try:
        graph_database = conn["graph-database"]
        mongo_collection = graph_database["graph-collection"]
        mongo_collection.replace_one({"_id": set_id}, graph_dictionary, upsert=True)
        print(f"Upsert {set_id} to Database")
    except TypeError as te:
        utils.print_error(te)
        ct.Errcodes.curr_errcode = ct.Errcodes.MONGODB_UPSERT_ERROR
