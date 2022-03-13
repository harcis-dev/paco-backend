from paco.configs.configs import EpcLabels
from paco.databases.mariadb_services.mariadb_service import functions
from paco.model.basis_graph import deep_merge_two_dicts

# FIXME DEBUG
from paco.configs.configs import BpmnLabels


# ---


def create_bpmn(basis_graph):
    bpmn = basis_graph.graph

    edges = basis_graph.edges
    id_edges = basis_graph.id_edges
    events_by_index = basis_graph.events_by_index
    # variants of the start node
    all_variants = bpmn["graph"][0]["data"]["variants"]

    print("\nTranslating to BPMN")

    # add the end event
    end_id = "End"
    bpmn["graph"].append({"data": {"id": end_id, "parent": BpmnLabels.PROCESS, "type": BpmnLabels.END,
                                   "label": "", "variants": all_variants}})
    events_by_index[end_id] = len(bpmn["graph"]) - 1

    # add the join xor node
    xor_node_id = f'{end_id}_XOR_JOIN'
    bpmn["graph"].append(
        {"data": {"id": xor_node_id, "parent": BpmnLabels.PROCESS, "type": "XOR",  # will be renamed
                  "label": "X", "variants": all_variants}})
    events_by_index[xor_node_id] = len(bpmn["graph"]) - 1

    # add an edge from the xor node to the end event
    new_edge_xor_end = {
        "data": {"id": f"{xor_node_id}_{end_id}", "source": xor_node_id,
                 "target": end_id, "type": BpmnLabels.EDGE, "variants":  all_variants}}
    edges.append(new_edge_xor_end)

    # remember the index of the inserted (xor -> end)-edge in edges
    edges_idx_xor_end = len(edges) - 1

    id_edges["in"][end_id] = {}
    id_edges["in"][end_id][edges_idx_xor_end] = new_edge_xor_end
    id_edges["out"][xor_node_id] = {}
    id_edges["in"][xor_node_id] = {}
    id_edges["out"][xor_node_id][edges_idx_xor_end] = new_edge_xor_end

    # connect all leaves with the xor node
    for node in bpmn["graph"]:
        if node is None:
            continue
        # if a leaf
        node_id = node["data"]["id"]
        if node_id not in id_edges["out"] and node_id != end_id:
            # add an edge from the leaf to the xor node
            new_edge_leaf_xor = {
                "data": {"id": f"{node_id}_{xor_node_id}", "source": node_id,
                         "target": xor_node_id, "type": BpmnLabels.EDGE, "variants": node["data"]["variants"]}}
            edges.append(new_edge_leaf_xor)

            # remember an index of the inserted (leaf -> xor)-edge in edges
            edges_idx_leaf_xor = len(edges) - 1

            id_edges["in"][xor_node_id][edges_idx_leaf_xor] = new_edge_leaf_xor
            id_edges["out"][node_id] = {}
            id_edges["out"][node_id][edges_idx_leaf_xor] = new_edge_leaf_xor

    # merge identical nodes as successors of split xor operators and their successors
    basis_graph.merge_paths("bpmn")

    print("removing None values")
    temp = []
    for node in bpmn["graph"]:
        if node is not None:
            temp.append(node)
    bpmn["graph"] = temp

    print("\nRenaming attributes")

    # rename attributes
    for node in bpmn["graph"]:
        node["data"]["parent"] = BpmnLabels.PROCESS
        if node["data"]["type"] != "XOR":
            if node["data"]["id"] != "start" and node["data"]["id"] != end_id:
                # activities
                node["data"]["type"] = BpmnLabels.ACTIVITY
                node["data"]["label"] = f"{node['data']['label']} {BpmnLabels.ACTIVITY_LABEL}"
            else:
                # start event
                del node["data"]["label"]
                node["data"]["type"] = BpmnLabels.START
        else:
            # xor
            del node["data"]["label"]
            node["data"]["type"] = BpmnLabels.XOR

    # adding the process pool
    # TODO PROCESS LABEL
    process = {"data": {"id": BpmnLabels.PROCESS, "label": "A Wonderful Process",
                        "variants": all_variants}}

    # add the process pool to the graph
    bpmn["graph"].append(process)
    events_by_index[BpmnLabels.PROCESS] = len(bpmn["graph"]) - 1

    # add edges to the graph
    for edge in edges:
        if edge is not None:
            edge["data"]["type"] = BpmnLabels.EDGE
            bpmn["graph"].append(edge)

    print("graph created")

    return bpmn