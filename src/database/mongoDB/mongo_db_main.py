import os
import sys

from pymongo import MongoClient, errors
conn = None

def init_database():
    try:
        global conn
        conn = MongoClient(
            host=os.environ['MONGODB_DOMAIN'],
            port=int(os.environ['MONGODB_PORT']),
            username=os.environ['MONGO_ROOT_USER'],
            password=os.environ['MONGO_ROOT_PASSWORD'],
        )
        print("Debug: Database connection established")
        return True
    except errors.PyMongoError as e:
        print(f"Error connecting to MongoDB Platform: {e}")
        sys.exit(1)

def get_something_from_database():
    print("MondoDB-Server version:", conn.server_info()["version"])
    database_names = conn.list_database_names()
    print("\ndatabases:", database_names)
    mydb = conn["Datenbank"]
    mycol = mydb["Tabelle"]
    abstract = { "nodes": [1, 2, 3] , "edges": ['a', 'b', 'c']}
    epk = { "nodes": [1, 2, 3] , "edges": ['a', 'b', 'c']}
    bpmn = { "nodes": [1, 2, 3] , "edges": ['a', 'b', 'c']}
    mydict = {"abstract": abstract, "epk": epk, "bpmn": bpmn}
    x = mycol.insert_one(mydict)
    # mydb[mycol].createIndex({"SAP-ID": 1}, unique=True)
    # for i in mycol.find():
    #     print(i)
