from itertools import islice

from src.configs.configs import EpcLabels
from src.databases.mariadb_services.mariadb_service import functions
from src.model.event import Event
from src.model.eventnode import EventNode


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

    # the start node has all the variants
    all_variants = epc["graph"][0]["data"]["variants"]

    print("\nAdding functions")
    id_iter = 0
    for node in islice(epc["graph"], 0, len(epc["graph"]) - 1):
        node_id = node["data"]["id"]
        if "_XOR_" in node_id:
            continue
        node_label = node["data"]["label"]
        node_variants = node["data"]["variants"]
        node["data"]["type"] = EpcLabels.EVENT
        if node_id != "start":
            node["data"]["label"] = f"{node_label} {EpcLabels.EVENT_LABEL}"

            function_id = f"{node_id}_{id_iter}_{node_label}_function"
            function_node = {"data": {"id": function_id, "label": f"{functions(list(node_variants)[0])}", "type": EpcLabels.FUNCTION,
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
