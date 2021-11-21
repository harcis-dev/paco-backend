from flask import Flask, request
import time

from databases.mariadb_services import mariadb_service as mariadb
from databases.mongodb_services import mongodb_service as mongodb
from src.eventlog.sapdata import read_sap_data
from src.graphs.dfgbuilder import create_dfg
from src.graphs.epcbuilder import create_epc
from src.configs import configs as ct

app = Flask(__name__)

@app.route('/graphs')
def calculate_new_graph():  # put application's code here
    start = time.time()

    init()

    end = time.time()
    request_duration = (end - start)
    print(f"\n<--- Execution duration: {request_duration} --->")
    # response.headers.add("Access-Control-Allow-Origin", "*")
    return 'Der Graph ist fertig!', 204


def init():
    ct.set_language('E')
    filters = request.args.getlist('filters')
    cases, variants = read_sap_data(filters)
    #print(sd.cases)
    dfg = create_dfg(variants)
    print("Dfg initiated, start creating the graph...")
    #print(f"Dfg created:\n{dfg.dfg_dict}")

    epc = create_epc(variants)
    print("Epc initiated, start creating the graph...")
#   print(f"Epc created:\n{epc.epc_dict}")
    #with open('data50dfg.json', 'w') as f:
    #    json.dump(dfg.dfg_dict, f)
    graph_dictionary = {"dfg": dfg, "epc": epc, "bpmn": {}}

    mongodb.upsert("5", graph_dictionary)

    print("Graphes stored")


if __name__ == '__main__':
    mariadb.init_database()  # Connect to MariaDB
    mongodb.init_database()  # Connect to MongoDB
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
