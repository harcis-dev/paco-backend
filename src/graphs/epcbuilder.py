from itertools import islice

from src.configs.configs import EpcLabels
from src.model.event import Event
from src.model.eventnode import EventNode


def create_epc(basis_graph):
    epc = {"graph": []}
    start_nodes = {}
    end_nodes = {}
    events_by_name = {}

    # edges will be added at the end of the graph creation,
    # so that they are placed separate from the nodes in the back part of the pm["graph"] array
    edges = []
    # event id with their edges
    id_edges = {"in": {}, "out": {}}



    # translating to epc
    print("Translating to EPC")

    # adding the start node
    start_nodes = {}
    all_variants = {}
    for node in epc["graph"]:
        node_id = node["data"]["id"]
        node_variants = node["data"]["variants"]
        # if no in-edges then a start node
        if not (node_id in id_edges["in"] and id_edges["in"][node_id]):
            start_nodes[node_id] = node_variants

        # add variants of the current node to all variants
        # {"2": {"001_1": "", "001_2": ""},
        #  "3": {"001_3": ""}}
        # and
        # {"2": {"001_1": "", "001_3": ""}}
        # equals
        # {"2": {"001_1": "", "001_2": "", "001_3": ""},
        #  "3": {"001_3": ""}}
        for variant_id in node_variants:
            # "update" is union of dictionary keys;
            # if there is no all_variants[variant_id]
            # it just takes node_variants[variant_id]
            all_variants.setdefault(variant_id, {}).update(node_variants[variant_id])

    artificial_start_node = {"data": {"id": "start", "label": EpcLabels.START, "type": EpcLabels.EVENT,
                                      "variants": all_variants}}
    epc["graph"].append(artificial_start_node)
    print("Start node added")

    if len(start_nodes) > 1:
        xor_node_id = f"start_XOR_SPLIT"

        # add the xor node to the graph
        epc["graph"].append(
            {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                      "variants": all_variants}})
        print("Split xor added")

        # add an edge between the start node and the xor node
        new_edge_start_xor = {
            "data": {"source": "start", "target": xor_node_id, "label": "",
                     "type": "DirectedEdge", "variants": all_variants}}
        edges.append(new_edge_start_xor)

        edges_idx_start_xor = len(edges) - 1
        id_edges["out"]["start"] = {}
        id_edges["out"]["start"][edges_idx_start_xor] = new_edge_start_xor
        id_edges["in"][xor_node_id] = {}
        id_edges["in"][xor_node_id][edges_idx_start_xor] = new_edge_start_xor

        # edges from xor node to successors of the start node
        id_edges["out"][xor_node_id] = {}
        for startsucc_id in start_nodes:
            new_edge_xor_startsucc = {
                "data": {"source": xor_node_id, "target": startsucc_id, "label": "",
                         "type": "DirectedEdge", "variants": start_nodes[startsucc_id]}}
            edges.append(new_edge_xor_startsucc)
            print(f"Start to {startsucc_id} edge added")

            edges_idx_xor_startsucc = len(edges) - 1
            id_edges["out"][xor_node_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
            id_edges["in"][startsucc_id] = {}
            id_edges["in"][startsucc_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
    else:
        # add an edge from the start node to its successor
        target_node = next(iter(start_nodes))
        new_edge_start_startsucc = {"data": {"source": "start", "target": target_node, "label": "",
                                             "type": "DirectedEdge", "variants": start_nodes[target_node]}}
        edges.append(new_edge_start_startsucc)
        print(f"Start to {target_node} edge added")
        edges_idx_start_startsucc = len(edges) - 1
        id_edges["out"]["start"][edges_idx_start_startsucc] = new_edge_start_startsucc
        id_edges["in"][target_node] = {}
        id_edges["in"][target_node][edges_idx_start_startsucc] = new_edge_start_startsucc

    print("\nAdding functions")
    id_iter = 0
    for node in epc["graph"]:
        node_id = node["data"]["id"]
        node_type = node["data"]["type"]
        node_label = node["data"]["label"]
        node_variants = node["data"]["variants"]
        if node_type == EpcLabels.EVENT:
            if node_id != "start":
                node["data"]["label"] = f"{node_label} {EpcLabels.EVENT_LABEL}"

                function_id = f"{node_id}_{id_iter}_{node_label}_function"
                function_node = {"data": {"id": function_id, "label": node_label, "type": EpcLabels.FUNCTION,
                                          "variants": all_variants}}

                # add the function node to the graph
                epc["graph"].append(function_node)
                print(f"Function {function_id} added")

                # add an edge between the function node and the current node
                new_edge_func_curnode = {"data": {"source": function_id, "target": node_id, "label": "",
                                                  "type": "DirectedEdge", "variants": node_variants}}
                edges.append(new_edge_func_curnode)

                # remember an index of the inserted (function node -> current node)-edge in edges
                edges_idx_func_curnode = len(edges) - 1

                # edges from predecessors of the current node to the function node
                print(f"Adding edges from {function_id} to predecessors of {node_id}")
                id_edges["in"][function_id] = {}
                for edges_idx, edge in id_edges["in"][node_id].items():
                    source_node = edge["data"]["source"]
                    new_edge_curnodepred_func = {
                        "data": {"source": source_node, "target": function_id, "label": "",
                                 "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                    edges.append(new_edge_curnodepred_func)

                    # remember an index of the inserted (current node pred -> function node)-edge in edges
                    edges_idx_curnodepred_func = len(edges) - 1

                    id_edges["in"][function_id][edges_idx_curnodepred_func] = new_edge_curnodepred_func
                    id_edges["out"][source_node][edges_idx_curnodepred_func] = new_edge_curnodepred_func

                    # remove the old edge from the graph;
                    # the old ones will be replaced with None so as not to disrupt indexing
                    edges[edges_idx] = None

                    # remove the old out-edge from the source node
                    del id_edges["out"][source_node][edges_idx]

                print("Function and predecessors are connected")

                # update in and out edge lists with the (xor -> current node)-edge
                id_edges["in"][node_id] = {}  # remove all the old edges
                id_edges["in"][node_id][edges_idx_func_curnode] = new_edge_func_curnode
                id_edges["out"][function_id] = {}
                id_edges["out"][function_id][edges_idx_func_curnode] = new_edge_func_curnode

                id_iter += 1

    for edge in edges:
        if edge is not None:
            print(f'{edge["data"]["source"]} -> {edge["data"]["target"]}')
            epc["graph"].append(edge)

    print("graph created")

    return epc
