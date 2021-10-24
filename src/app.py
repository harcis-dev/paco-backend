from flask import Flask, jsonify, request
# from flask_cors import CORS
import time
from databases.mariadb_services import mariadb_service as mariadb
from databases.mongodb_services import mongodb_service as mongodb
from src.eventlog.sapdata import SapData
from src.graphs.processmodel import ProcessModel

app = Flask(__name__)


# CORS(app, resources={r"/api-py/*": {"origins": "*"}})


@app.route('/new-data')
def calculate_new_graph():  # put application's code here
    # FIXME DEBUG
    mariadb.init_database()  # Connect to MariaDB
    mongodb.init_database()  # Connect to MongoDB
    # ---

    start = time.time()

    filters = request.args.getlist('filters')
    se = SapData()
    se.read_data(filters)
    #print(se.cases)
    pm = ProcessModel(se.variants)
    print("Process model initiated, start creating the graph...")
    pm.create()
    print(f"Process model created:\n{pm.pm_dict}")

    graph_dictionary = {"dfg": pm.pm_dict, "epc": "", "bpmn": ""}

    mongodb.upsert(1, graph_dictionary)

    print("Graphes stored")

    end = time.time()
    request_duration = (end - start)
    print(f"\n<--- Execution duration: {request_duration} --->")
    # response.headers.add("Access-Control-Allow-Origin", "*")
    return '', 204


if __name__ == '__main__':
    app.run()
    '''
    # example insert
    generally = {"nodes": [1, 2, 3], "edges": ['aaaaa', 'b', 'c']}
    epk = {"nodes": [1, 2, 3], "edges": ['a', 'b', 'c']}
    bpmn = {"nodes": [1, 2, 3], "edges": ['a', 'b', 'c']}
    graph_dictionary = {"generally": generally, "epk": epk, "bpmn": bpmn}
    mongodb.upsert(1, graph_dictionary)
    # ---
    '''