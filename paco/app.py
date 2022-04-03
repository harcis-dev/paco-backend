import json
import os

import flask
import jsonpickle
import requests as requests

from flask import Flask, request
import time
import datetime

from paco.databases.mariadb_services import mariadb_service as mariadb
from paco.databases.mongodb_services import mongodb_service as mongodb
from paco.eventlog import sapdata as sapdata
from paco.eventlog import csvdata as csvdata

# FIXME DEBUG
from paco.graphs.bpmnbuilder import create_bpmn
from paco.graphs.epcbuilder import create_epc
from paco.model.event import Event
from paco.model.case import Case
from paco.model.variant import Variant
# ---

from paco.utils import configs as ct, utils
from paco.graphs.dfgbuilder import create_dfg
from paco.model.basis_graph import BasisGraph
from paco.utils.blueprints import paco_bp

import copy

#@paco_bp.route('/graphs', methods=["GET", "POST"])
@paco_bp.route('/')
def get_graphs():
    # Logging
    import logging
    import os
    log_filename = "paco_logs/paco_debug.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logging.FileHandler(log_filename, mode="w", encoding=None, delay=False)
    logging.basicConfig(filename="paco_logs/paco_debug.log", level=logging.DEBUG)
    logging.debug("I'm debug, I'm alive")
    # -----------

    start = time.time()

    is_csv = False

    try:
        if request.method == "GET":
            if ct.Configs.EPC_EXAMP:
                variants = gen_test_variants_epc()
            elif ct.Configs.REPRODUCIBLE:
                if not os.path.exists(f"casesvariants.json"):
                    cases, variants = sapdata.read_sap_data(None)
                    with open('casesvariants.json', 'w') as f:
                        variants_json = jsonpickle.encode(variants)
                        json.dump(variants_json, f)
                else:
                    with open('casesvariants.json', 'r') as f:
                        variants_json = json.load(f)
                        variants = jsonpickle.decode(variants_json)
            else:
                cases, variants = sapdata.read_sap_data(None)
        elif request.method == "POST":
            is_csv = True
            try:
                file = request.files['file']
            except KeyError:
                return 'No file uploaded!', 400
            variants = csvdata.parse_csv(file)
        else:
            variants = []

        create_graphs(variants, is_csv)
    except Exception as ex:
        utils.print_error(ex)
        if ct.Errcodes.curr_errcode == 0:
            # general error
            ct.Errcodes.curr_errcode = ct.Errcodes.UNEXPECTED_ERROR

    end = time.time()
    request_duration = (end - start)
    print(f"\n<--- Execution duration: {request_duration} --->")
    # response.headers.add("Access-Control-Allow-Origin", "*")

    return ('Ready!', 204) if ct.Errcodes.curr_errcode == 0 else (ct.Errcodes.ERR_MESSAGES[ct.Errcodes.curr_errcode], 500)


#@paco_bp.route('/')
#def default_route():
#    return "Use '/graphs'", 418


def create_graphs(variants, is_csv):
    if not variants:  # None or []
        return None

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

    now = datetime.datetime.now().strftime('%d-%m-%y_%H:%M:%S')
    graph_dictionary = {"name": "graph_"+now, "dfg": dfg, "epc": epc, "bpmn": bpmn}
    mongodb.upsert_graphs("graph_"+now, graph_dictionary)

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
    paco_bp.run()
