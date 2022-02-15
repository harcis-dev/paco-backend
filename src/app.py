import json

from flask import Flask, request
import time

from databases.mariadb_services import mariadb_service as mariadb
from databases.mongodb_services import mongodb_service as mongodb
from src.eventlog.sapdata import read_sap_data

# FIXME DEBUG
from src.graphs.epcbuilder import create_epc
from src.model.event import Event
from src.model.case import Case
from src.model.variant import Variant
# ---

from src.configs import configs as ct
from src.graphs.dfgbuilder import create_dfg
from src.model.basis_graph import BasisGraph

import copy

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

    if ct.Configs.DEBUG:
        variants = gen_test_variants() # FIXME DEBUG
    else:
        cases, variants = read_sap_data(filters)

    ''' DEBUG '''
    #print(sd.cases)
    #dfg = create_dfg(variants)
    #print("Dfg initiated, start creating the graph...")
    #print(f"Dfg created:\n{dfg.dfg_dict}")

    basis_graph = BasisGraph()
    basis_graph.create_basis_graph(variants)
    print(f"\nBasis graph created")

    copy_basis_graph = copy.deepcopy(basis_graph)
    epc = create_epc(basis_graph)
    print(f"\nEpc created")

    #with open('data5000basis.json', 'w') as f:
    #    json.dump(basis_graph.graph, f)

    #graph_dictionary = {"dfg": dfg}
    graph_dictionary = {"dfg": copy_basis_graph.graph, "epc": epc}

    #mongodb.upsert(str(size)+"_basis", graph_dictionary)
    mongodb.upsert("test5", graph_dictionary)

    print("Graphes stored")

# FIXME DEBUG
def gen_test_variants():
    event_A1 = Event("A_1", "A")
    event_B1 = Event("B_1", "B")
    event_C1 = Event("C_1", "C")
    event_D1 = Event("D_1", "D")

    event_A2 = Event("A_2", "A")
    event_B2 = Event("B_2", "B")
    event_C2 = Event("C_2", "C")

    event_A3 = Event("A_3", "A")
    event_B3 = Event("B_3", "B")
    event_C3 = Event("C_3", "C")

    event_A4 = Event("A_4", "A")
    event_E1 = Event("E_1", "E")

    case_ABCD = Case("Case_ABCD")
    case_ABCD.events.append(event_A1)
    case_ABCD.events.append(event_B1)
    case_ABCD.events.append(event_C1)
    case_ABCD.events.append(event_D1)

    case_ABC1 = Case("Case_ABC_1")
    case_ABC1.events.append(event_A2)
    case_ABC1.events.append(event_B2)
    case_ABC1.events.append(event_C2)

    case_ABC2 = Case("Case_ABC_2")
    case_ABC2.events.append(event_A3)
    case_ABC2.events.append(event_B3)
    case_ABC2.events.append(event_C3)

    case_AE = Case("Case_AE")
    case_AE.events.append(event_A4)
    case_AE.events.append(event_E1)

    variant_ABCD = Variant(case_ABCD)

    variant_ABC = Variant(case_ABC1)
    variant_ABC.cases.append(case_ABC2)

    variant_AE = Variant(case_AE)

    return [variant_ABCD, variant_ABC, variant_AE]

if __name__ == '__main__':
    mariadb.init_database()  # Connect to MariaDB
    mongodb.init_database()  # Connect to MongoDB
    #sys.setrecursionlimit(2000)
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
