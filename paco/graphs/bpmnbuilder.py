from paco.utils.configs import BpmnLabels


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

    # indexes of the nodes without successors (graph leaves)
    leaves = []
    for node_idx, node in enumerate(bpmn["graph"]):
        if node is None:
            continue
        # if a leaf
        node_id = node["data"]["id"]
        if node_id not in id_edges["out"] and node_id != end_id:
            leaves.append(node_idx)

    if len(leaves) == 1:  # only one leaf
        # add an edge from that leaf to the end event
        leaf_id = bpmn["graph"][leaves[0]]["data"]["id"]
        new_edge_leaf_end = {
            "data": {"id": f"{leaf_id}_{end_id}", "source": leaf_id,
                     "target": end_id, "type": BpmnLabels.EDGE, "variants": all_variants}}
        edges.append(new_edge_leaf_end)

        # remember the index of the inserted (leaf -> end)-edge in edges
        edges_idx_leaf_end = len(edges) - 1

        id_edges["in"][end_id] = {}
        id_edges["in"][end_id][edges_idx_leaf_end] = new_edge_leaf_end
        id_edges["out"][leaf_id] = {}
        id_edges["out"][leaf_id][edges_idx_leaf_end] = new_edge_leaf_end
    else:
        # add a join xor node
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
        for leaf_idx in leaves:
            leaf = bpmn["graph"][leaf_idx]
            leaf_id = leaf["data"]["id"]
            # add an edge from the leaf to the xor node
            new_edge_leaf_xor = {
                "data": {"id": f"{leaf_id}_{xor_node_id}", "source": leaf_id,
                         "target": xor_node_id, "type": BpmnLabels.EDGE, "variants": leaf["data"]["variants"]}}
            edges.append(new_edge_leaf_xor)

            # remember an index of the inserted (leaf -> xor)-edge in edges
            edges_idx_leaf_xor = len(edges) - 1

            id_edges["in"][xor_node_id][edges_idx_leaf_xor] = new_edge_leaf_xor
            id_edges["out"][leaf_id] = {}
            id_edges["out"][leaf_id][edges_idx_leaf_xor] = new_edge_leaf_xor

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