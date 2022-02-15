from itertools import islice

from src.configs.configs import EpcLabels
from src.databases.mariadb_services.mariadb_service import functions
from src.model.basis_graph import deep_merge_two_dicts
from src.model.event import Event
from src.model.eventnode import EventNode

# FIXME DEBUG
from src.configs import configs as ct


# ---


def create_epc(basis_graph):
    epc = basis_graph.graph

    # edges will be added at the end of the graph creation,
    # so that they are placed separate from the nodes in the back part of the pm["graph"] array
    edges = basis_graph.edges
    # event id with their edges
    id_edges = basis_graph.id_edges

    # translating to epc
    print("Translating to EPC")

    # renaming the start node
    print("Renaming the start node")
    epc["graph"][0]["data"]["label"] = EpcLabels.START

    print("\nAdding functions")
    id_iter = 0

    for node in islice(epc["graph"], 0, len(epc["graph"])):
        node_id = node["data"]["id"]
        if node["data"]["type"] != "XOR":
            node["data"]["type"] = EpcLabels.EVENT
            if node_id != "start":
                node_label = node["data"]["label"]
                node_variants = node["data"]["variants"]
                node["data"]["label"] = f"{node_label} {EpcLabels.EVENT_LABEL}"

                function_id = f"{node_id}_{id_iter}_{node_label}_function"
                function_label = functions(list(node_variants)[0]) if not ct.Configs.DEBUG else node_label
                function_node = {"data": {"id": function_id, "label": f"{function_label}", "type": EpcLabels.FUNCTION,
                                          "variants": node_variants}}

                # add the function node to the graph
                epc["graph"].append(function_node)
                basis_graph.events_by_index[function_id] = len(epc["graph"]) - 1
                print(f"Function {function_id} added")

                # add an edge between the function node and the current node
                new_edge_func_curnode = {
                    "data": {"id": f"{function_id}_{node_id}", "source": function_id, "target": node_id, "label": "",
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
                        "data": {"id": f"{source_node}_{function_id}", "source": source_node, "target": function_id,
                                 "label": "", "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
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
            else:
                node["data"]["label"] = EpcLabels.START_LABEL
        else:  # XOR
            # only a function can precede a split XOR operator,
            # so insert if necessary
            if "_XOR_SPLIT" in node_id:  # if the node is a split xor operator
                node_variants = node["data"]["variants"]
                for edges_idx, edge in id_edges["in"][node_id].items():
                    # if a predecessor of the xor node is not already a function
                    # (it is impossible for the current state of the program,
                    #  but anyway it is worth checking)
                    pred_id = edge["data"]["source"]
                    pred_graph_idx = basis_graph.events_by_index[pred_id]
                    if epc["graph"][pred_graph_idx]["data"]["type"] != EpcLabels.FUNCTION:
                        function_id = f"{node_id}_{id_iter}_X_function"
                        function_label = f"{functions(list(node_variants)[0])} {EpcLabels.SPLIT_FUNCTION}" if not ct.Configs.DEBUG else f"SPLIT XOR {EpcLabels.SPLIT_FUNCTION}"
                        function_node = {
                            "data": {"id": function_id, "label": f"{function_label}", "type": EpcLabels.FUNCTION,
                                     "variants": node_variants}}

                        # add the function node to the graph
                        epc["graph"].append(function_node)
                        basis_graph.events_by_index[function_id] = len(epc["graph"]) - 1
                        print(f"Function {function_id} added")

                        # add an edge between the function node and the xor node
                        new_edge_func_xor = {
                            "data": {"id": f"{function_id}_{node_id}", "source": function_id, "target": node_id,
                                     "label": "", "type": "DirectedEdge", "variants": node_variants}}
                        edges.append(new_edge_func_xor)

                        # remember an index of the inserted (function node -> xor)-edge in edges
                        edges_idx_func_xor = len(edges) - 1

                        # edges from predecessors of the current node to the function node
                        print(f"Adding edges from {function_id} to predecessors of {node_id}")
                        id_edges["in"][function_id] = {}
                        for edges_idx_func, edge_func in id_edges["in"][node_id].items():
                            source_node = edge_func["data"]["source"]
                            new_edge_xorpred_func = {
                                "data": {"id": f"{source_node}_{function_id}", "source": source_node,
                                         "target": function_id, "label": "",
                                         "type": "DirectedEdge", "variants": edge_func["data"]["variants"]}}
                            edges.append(new_edge_xorpred_func)

                            # remember an index of the inserted (xor pred -> function node)-edge in edges
                            edges_idx_xorpred_func = len(edges) - 1

                            id_edges["in"][function_id][edges_idx_xorpred_func] = new_edge_xorpred_func
                            id_edges["out"][source_node][edges_idx_xorpred_func] = new_edge_xorpred_func

                            # remove the old edge from the graph;
                            # the old ones will be replaced with None so as not to disrupt indexing
                            edges[edges_idx_func] = None

                            # remove the old out-edge from the source node
                            del id_edges["out"][source_node][edges_idx_func]

                        print("Function and predecessors are connected")

                        # update in and out edge lists with the (xor -> current node)-edge
                        id_edges["in"][node_id] = {}
                        id_edges["in"][node_id][edges_idx_func_xor] = new_edge_func_xor
                        id_edges["out"][function_id] = {}
                        id_edges["out"][function_id][edges_idx_func_xor] = new_edge_func_xor

                        id_iter += 1

    # if some successors of a split xor node are identical,
    # they will be merged
    changed = True
    while changed:
        changed = False
        for node in epc["graph"]:
            if node is None:
                continue  # one of deleted xor successors

            node_id = node["data"]["id"]
            node_type = node["data"]["type"]
            if "_XOR_SPLIT" in node_id and node_type == "XOR":
                # successor label -> [successor index, successor xor index, succ->xor edge index]
                unique_events = {}
                # check all the xor successors
                for edges_idx_succ, edge_succ in id_edges["out"][node_id].copy().items():
                    succ_id = edge_succ["data"]["target"]
                    succ_idx = basis_graph.events_by_index[succ_id]
                    succ_label = epc["graph"][succ_idx]["data"]["label"]

                    if succ_label not in unique_events:
                        unique_events[succ_label] = [succ_idx, None, None]
                    else:
                        # add successor xor node
                        if succ_id in id_edges["out"]:  # if the current successor has successors
                            changed = True
                            if unique_events[succ_label][1] is None:  # if no xor added
                                # adding xor
                                xor_node_id = f'{epc["graph"][unique_events[succ_label][0]]["data"]["label"]}_XOR_SPLIT'
                                epc["graph"].append(
                                    {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                              "variants": None}})  # variants will be added later
                                unique_events[succ_label][1] = len(epc["graph"]) - 1
                                basis_graph.events_by_index[xor_node_id] = unique_events[succ_label][1]

                                cur_node_id = epc["graph"][unique_events[succ_label][0]]["data"]["id"]

                                # add an edge between the xor node and successors of the current node
                                for edges_idx_succ, edge_succ in id_edges["out"][cur_node_id].items():
                                    succ_node = edge_succ["data"]["target"]
                                    new_edge_xor_curnodesucc = {
                                        "data": {"id": f"{xor_node_id}_{succ_node}", "source": xor_node_id,
                                                 "target": succ_node, "label": "",
                                                 "type": "DirectedEdge", "variants": edge_succ["data"]["variants"]}}
                                    edges.append(new_edge_xor_curnodesucc)

                                    # remember an index of the inserted (current node pred -> function node)-edge in edges
                                    edges_idx_xor_curnodesucc = len(edges) - 1

                                    id_edges["in"][succ_node][edges_idx_xor_curnodesucc] = new_edge_xor_curnodesucc
                                    id_edges["out"][xor_node_id] = {}
                                    id_edges["out"][xor_node_id][edges_idx_xor_curnodesucc] = new_edge_xor_curnodesucc

                                    # remove the old edge from the graph;
                                    # the old ones will be replaced with None so as not to disrupt indexing
                                    edges[edges_idx_succ] = None

                                    # remove the old in-edge of the succesor of the current node
                                    del id_edges["in"][succ_node][edges_idx_succ]
                                    # the old out-edge of the current node was already removed

                                # add an edge between the current node and the xor node
                                new_edge_cur_xor = {
                                    "data": {"id": f"{cur_node_id}_{xor_node_id}", "source": cur_node_id,
                                             "target": xor_node_id, "label": "",
                                             "type": "DirectedEdge", "variants": None}}  # variants will be added later
                                edges.append(new_edge_cur_xor)

                                # remember an index of the inserted (current node -> xor)-edge in edges
                                edge_idx_cur_xor = len(edges) - 1
                                unique_events[succ_label][2] = edge_idx_cur_xor

                                # add the edge to the in and out edges of the nodes
                                id_edges["out"][unique_events[succ_label][0]] = {}
                                id_edges["out"][unique_events[succ_label][0]][edge_idx_cur_xor] = new_edge_cur_xor
                                id_edges["in"][xor_node_id] = {}
                                id_edges["in"][xor_node_id][edge_idx_cur_xor] = new_edge_cur_xor

                            # add an edge between the xor node and the successor of the identical node
                            for edge_idx_idec, edge_idec in id_edges["out"][succ_id].items():
                                succ_idec = edge_idec["data"]["target"]
                                xor_node_id = epc["graph"][unique_events[succ_label][1]]["data"]["id"]
                                new_edge_xor_succidec = {
                                    "data": {"id": f"{xor_node_id}_{succ_idec}", "source": xor_node_id,
                                             "target": succ_idec, "label": "", "type": "DirectedEdge",
                                             "variants": edge_idec["data"]["variants"]}}
                                edges.append(new_edge_xor_succidec)

                                # remember an index of the inserted (xor -> successor of the identical node)-edge in edges
                                edge_idx_xor_succidec = len(edges) - 1

                                id_edges["out"][xor_node_id][edge_idx_xor_succidec] = new_edge_xor_succidec
                                id_edges["in"][succ_idec][edge_idx_xor_succidec] = new_edge_xor_succidec

                            # add all variants to one of identical xor successors
                            epc["graph"][unique_events[succ_label][0]]["data"]["variants"] = deep_merge_two_dicts(
                                epc["graph"][unique_events[succ_label][0]]["data"]["variants"],
                                epc["graph"][succ_idx]["data"]["variants"])

                            # remove the identical xor successor (current node)
                            remove_node(epc, succ_idx, basis_graph.events_by_index, edges, id_edges)

                # set variants of the added xors and edges between xors and unique nodes
                for succ_xor in unique_events.values():
                    if succ_xor[1] is not None:
                        succ_variants = epc["graph"][succ_xor[0]]["data"]["variants"]
                        in_edge = list(id_edges["in"][epc["graph"][succ_xor[0]]["data"]["id"]].values())[0]
                        in_edge["data"]["variants"] = succ_variants
                        epc["graph"][succ_xor[1]]["data"]["variants"] = succ_variants
                        edges[succ_xor[2]]["data"]["variants"] = succ_variants

                # if all the successors of the split xor were identical,
                # remove the xor operator
                if len(id_edges["out"][node_id]) == 1:
                    for edge_idx_xor, edge_xor in id_edges["in"][node_id].items():
                        pred_xor_id = edge_xor["data"]["source"]
                        succ_xor_idx = list(unique_events.values())[0][0]  # only one unique event
                        succ_xor_id = epc["graph"][succ_xor_idx]["data"]["id"]
                        new_edge_predxor_succxor = {
                            "data": {"id": f"{pred_xor_id}_{succ_xor_id}", "source": pred_xor_id,
                                     "target": succ_xor_id,
                                     "label": "",
                                     "type": "DirectedEdge",
                                     "variants": epc["graph"][succ_xor_idx]["data"]["variants"]}}
                        edges.append(new_edge_predxor_succxor)

                        # remember an index of the inserted (xor -> successor of the identical node)-edge in edges
                        edge_idx_predxor_succxor = len(edges) - 1

                        id_edges["out"][pred_xor_id][edge_idx_predxor_succxor] = new_edge_predxor_succxor
                        id_edges["in"][succ_xor_id][edge_idx_predxor_succxor] = new_edge_predxor_succxor

                    remove_node(epc, basis_graph.events_by_index[node_id], basis_graph.events_by_index, edges, id_edges)

            if changed: break

    print("removing None values")
    temp = []
    for node in epc["graph"]:
        if node is not None:
            temp.append(node)
    epc["graph"] = temp

    for edge in edges:
        if edge is not None:
            print(f'{edge["data"]["source"]} -> {edge["data"]["target"]}')
            epc["graph"].append(edge)

    print("graph created")

    return epc


def remove_node(graph, node_idx, events_by_index, edges, id_edges):
    node_id = graph["graph"][node_idx]["data"]["id"]
    graph["graph"][node_idx] = None
    del events_by_index[node_id]
    remove_edges(edges, id_edges, node_id, "in")
    remove_edges(edges, id_edges, node_id, "out")


def remove_edges(edges, id_edges, node_id, direction):
    if node_id in id_edges[direction]:
        edges_to_remove = id_edges[direction][node_id]
        for edge_idx_to_remove in edges_to_remove:
            if direction == "in":  # delete the corresponding out-edge of predecessor
                pred_id = edges[edge_idx_to_remove]["data"]["source"]
                if pred_id in id_edges["out"]:
                    del id_edges["out"][pred_id][edge_idx_to_remove]
            else:  # delete the corresponding in-edge of successor
                succ_id = edges[edge_idx_to_remove]["data"]["target"]
                if succ_id in id_edges["in"]:
                    del id_edges["in"][succ_id][edge_idx_to_remove]
            edges[edge_idx_to_remove] = None
        del id_edges[direction][node_id]
