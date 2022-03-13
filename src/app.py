import json
import os

import flask
import jsonpickle
import requests as requests

from flask import Flask, request
import time

from databases.mariadb_services import mariadb_service as mariadb
from databases.mongodb_services import mongodb_service as mongodb
import src.eventlog.sapdata as sapdata
import src.eventlog.csvdata as csvdata

# FIXME DEBUG
from src.graphs.bpmnbuilder import create_bpmn
from src.graphs.epcbuilder import create_epc
from src.model.event import Event
from src.model.case import Case
from src.model.variant import Variant
# ---

from src.configs import configs as ct
from src.graphs.dfgbuilder import create_dfg
from src.model.basis_graph import BasisGraph

import copy

paco = Flask(__name__)


@paco.route('/graphs', methods=["GET", "POST"])
def get_graphs():
    start = time.time()

    is_csv = False

    is_csv = True
    variants = csvdata.parse_csv("")

    create_graphs(variants, is_csv)

    end = time.time()
    request_duration = (end - start)
    print(f"\n<--- Execution duration: {request_duration} --->")
    # response.headers.add("Access-Control-Allow-Origin", "*")
    return 'Ready!', 204

def get_cases():
    string = requests.get('http://localhost:8080/api/event-log').content  # TODO
    return string


def create_graphs(variants, is_csv):
    ct.set_language('D')

    dfg = create_dfg(variants)
    print("\nDfg created")

    basis_graph = BasisGraph()
    basis_graph.create_basis_graph(variants)
    print("\nBasis graph created")

    copy_basis_graph_epc = copy.deepcopy(basis_graph)
    copy_basis_graph_bpmn = copy.deepcopy(basis_graph)

    epc = create_epc(copy_basis_graph_epc, is_csv)
    print("\nEpc created")

    bpmn = create_bpmn(copy_basis_graph_bpmn)
    print("\nBpmn created")

    # with open('data5000basis.json', 'w') as f:
    #    json.dump(basis_graph.graph, f)

    graph_dictionary = {"dfg": dfg, "epc": epc, "bpmn": bpmn}

    # mongodb.upsert(str(size)+"_basis", graph_dictionary)
    mongodb.upsert("debug_small", graph_dictionary)

    print("Graphes stored")


# FIXME DEBUG
def gen_test_variants_epc():
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


def gen_test_cases_epc():
    event_A1 = Event("A_1", "A")
    event_B1 = Event("B_1", "B")
    event_A2 = Event("A_2", "A")
    event_A3 = Event("A_3", "A")
    event_A4 = Event("A_4", "A")
    event_A1_A1 = Event("A_5", "A")
    event_A2_C1 = Event("C_1", "C")
    event_A3_C2 = Event("C_2", "C")

    case_AA = Case("Case_AA")
    case_AA.events.append(event_A1)
    case_AA.events.append(event_A1_A1)

    case_B = Case("Case_B")
    case_B.events.append(event_B1)

    case_AC1 = Case("Case_AC1")
    case_AC1.events.append(event_A2)
    case_AC1.events.append(event_A2_C1)

    case_AC2 = Case("Case_AC2")
    case_AC2.events.append(event_A3)
    case_AC2.events.append(event_A3_C2)

    case_A4 = Case("Case_A4")
    case_A4.events.append(event_A4)

    return [case_B, case_AC1, case_AC2, case_AA, case_A4]


def gen_test_cases_and_small():
    event_C1 = Event("C_1", "C")
    event_A1 = Event("A_1", "A")
    event_B1 = Event("B_1", "B")
    event_D1 = Event("D_1", "D")
    event_C2 = Event("C_2", "C")
    event_B2 = Event("B_2", "B")
    event_A2 = Event("A_2", "A")
    event_D2 = Event("D_2", "D")

    case_CABD = Case("Case_CABD")
    case_CABD.events.append(event_C1)
    case_CABD.events.append(event_A1)
    case_CABD.events.append(event_B1)
    case_CABD.events.append(event_D1)

    case_CBAD = Case("Case_CBAD")
    case_CBAD.events.append(event_C2)
    case_CBAD.events.append(event_B2)
    case_CBAD.events.append(event_A2)
    case_CBAD.events.append(event_D2)

    return [case_CABD, case_CBAD]


if __name__ == '__main__':
    mariadb.init_database()  # Connect to MariaDB
    mongodb.init_database()  # Connect to MongoDB
    paco.run()
