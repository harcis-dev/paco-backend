from paco.configs.configs import EpcLabels
from paco.databases.mariadb_services.mariadb_service import functions
from paco.model.basis_graph import deep_merge_two_dicts

# FIXME DEBUG
from paco.configs import configs as ct


# ---


def create_epc(basis_graph, is_csv):
    # merge identical successors of split xor nodes
    #basis_graph.merge_paths()

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
    epc["graph"][0]["data"]["label"] = EpcLabels.START_LABEL

    print("\nAdding functions")
    id_iter = 0

    # add a function before each event
    for node_idx in range(len(epc["graph"])):
        node = epc["graph"][node_idx]
        if node is None:
            continue  # removed node
        node_id = node["data"]["id"]
        if "_JOIN" not in node_id:
            # functions before split operators should have a special suffix
            function_label_suffix = ""
            if "_SPLIT" not in node_id:
                node["data"]["type"] = EpcLabels.EVENT
            elif "_XOR_SPLIT" in node_id:
                # if the predecessor node is not a function
                # add a function before the split operator node
                function_label_suffix = f" {EpcLabels.SPLIT_FUNCTION}"
                pred_id = next(iter(id_edges["in"][node_id].values()))["data"]["source"]
                pred_graph_idx = basis_graph.events_by_index[pred_id]
                # if already a function then skip
                if epc["graph"][pred_graph_idx]["data"]["type"] == EpcLabels.FUNCTION:
                    continue
            if node_id != "start":
                node_variants = node["data"]["variants"]
                node_label = node["data"]["label"]
                node_type = node["data"]["type"]
                node["data"]["label"] = f"{node_label} {EpcLabels.EVENT_LABEL}"

                function_id = f"{node_id}_{id_iter}_{node_label}_function"
                if not (ct.Configs.DEBUG or is_csv or node_type == "XOR"):
                    function_label = f"{functions(list(node_variants)[0])}{function_label_suffix}"
                else:
                    function_label = f"{node_label}{function_label_suffix}"
                function_node = {"data": {"id": function_id, "label": function_label, "type": EpcLabels.FUNCTION,
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
                    try:
                        del id_edges["out"][source_node][edges_idx]
                    except KeyError:
                        raise

                print("Function and predecessors are connected")

                # update in and out edge lists with the (xor -> current node)-edge
                id_edges["in"][node_id] = {}  # remove all the old edges
                id_edges["in"][node_id][edges_idx_func_curnode] = new_edge_func_curnode
                id_edges["out"][function_id] = {}
                id_edges["out"][function_id][edges_idx_func_curnode] = new_edge_func_curnode

                id_iter += 1
            else:
                node["data"]["label"] = EpcLabels.START_LABEL

    # merge identical nodes (functions as successors of split xor operators and their successors)
    basis_graph.merge_paths("epc")

    print("removing None values")
    temp = []
    for node in epc["graph"]:
        if node is not None:
            temp.append(node)
    epc["graph"] = temp

    for edge in edges:
        if edge is not None:
            print(f'{edge["data"]["source"]} -> {edge["data"]["target"]}')
            edge["data"]["type"] = EpcLabels.EDGE
            epc["graph"].append(edge)

    print("graph created")

    return epc