from itertools import islice

from src.configs.configs import EpcLabels
from src.model.event import Event
from src.model.eventnode import EventNode


def create_epc(variants):
    epc = {"graph": []}
    start_nodes = {}
    end_nodes = {}
    events_by_name = {}

    # edges will be added at the end of the graph creation,
    # so that they are placed separate from the nodes in the back part of the pm["graph"] array
    edges = []
    # event id with their edges
    id_edges = {"in": {}, "out": {}}

    for idx, variant in enumerate(variants):  # FIXME DEBUG REMOVE IDX
        var_event_pred = None
        event_node = None
        already_there = False
        for event_idx, var_event in enumerate(variant.events):
            event_ids = {}  # for event ids in cases
            found_node = None
            already_there = False

            # find all event ids (for each case) of the current event for the current variant
            for case in variant.cases:
                # the current event's index in the variant's list of events
                # corresponds to the current event's index in the case's list of events
                event_ids[case.id] = case.events[event_idx].id  # "case_0" : "event_id_0"
                if var_event.id.split("_")[0] != case.events[event_idx].id.split("_")[0]:
                    print(f"{var_event.id.split('_')[0]} vs {case.events[event_idx].id.split('_')[0]}")
                    print(f"variant events: {variant.events}")
                    print(f"case events: {case.events}")
                    raise

            if var_event.name in events_by_name:
                for event_by_name in events_by_name[var_event.name]:
                    if not event_by_name.has_this_predecessor(var_event_pred):
                        if event_idx != len(variant.events) - 1:
                            # successor of the current var_event
                            var_event_succ = variant.events[event_idx + 1]
                            if var_event_succ.name in events_by_name:
                                for event_succ_by_name in events_by_name[var_event_succ.name]:
                                    if event_by_name.has_this_successor(
                                            event_succ_by_name) and var_event_pred != event_by_name:
                                        if var_event_pred != event_by_name and bool(
                                                event_by_name.predecessors) == var_event_pred is not None:
                                            found_node = event_by_name
                                            break

                                if found_node is not None:
                                    event_node = found_node
                                    already_there = True
                                    break
                        else:
                            if var_event_pred is None == (not event_by_name.predecessors) and (
                                    not event_by_name.successors) and var_event_pred != event_by_name:
                                found_node = event_by_name
                                break

                            if found_node is not None:
                                event_node = found_node
                                already_there = True
                                break
                    else:
                        var_event_has_succ = event_idx != len(variant.events) - 1
                        if bool(event_by_name.successors) == var_event_has_succ and var_event_pred != event_by_name:
                            found_node = event_by_name
                            already_there = True
                            break

            if found_node is None:
                new_e = Event(f"{variant.id}_{event_idx}_{var_event.name}", var_event.name)

                epc["graph"].append(
                    {"data": {"id": new_e.id, "label": new_e.name, "type": EpcLabels.EVENT,
                              "variants": {variant.id: event_ids}}})

                # remember an index of the inserted node
                nodes_idx = len(epc["graph"]) - 1

                if new_e.name not in events_by_name:
                    events_by_name[new_e.name] = []

                found_node = EventNode(new_e, nodes_idx)
                events_by_name[new_e.name].append(found_node)
                print(f"new foundEvent: {found_node.event.id}")
            else:
                epc["graph"][found_node.nodes_idx]["data"]["variants"][variant.id] = event_ids
                print(f"foundEvent: {found_node.event.id}")

            event_node = found_node
            if var_event_pred is not None:
                var_event_pred.successors.append(event_node)
                event_node.predecessors.append(var_event_pred)

                # searching for an edge only if the event was found/is already in the graph
                found_edge = False
                for edge in edges:
                    if edge["data"]["source"] == var_event_pred.event.id and edge["data"][
                        "target"] == event_node.event.id:
                        # add the current variant to the map of variants of the edge
                        edge["data"]["variants"][variant.id] = event_ids
                        found_edge = True
                        break

                if not found_edge:
                    new_edge = {
                        "data": {"source": var_event_pred.event.id, "target": event_node.event.id, "label": "",
                                 "type": "DirectedEdge", "variants": {variant.id: event_ids}}}
                    edges.append(new_edge)

                    # remember an index of the inserted edge in edges
                    edges_idx = len(edges) - 1

                    if event_node.event.id not in id_edges["in"]:
                        id_edges["in"][event_node.event.id] = {}
                    id_edges["in"][event_node.event.id][edges_idx] = new_edge

                    if var_event_pred.event.id not in id_edges["out"]:
                        id_edges["out"][var_event_pred.event.id] = {}
                    id_edges["out"][var_event_pred.event.id][edges_idx] = new_edge

            elif not already_there:
                if var_event.name not in start_nodes:
                    start_nodes[var_event.name] = {}
                start_nodes[var_event.name][event_node.event.id] = event_node.nodes_idx

            var_event_pred = event_node

        if not already_there:
            if event_node.event.name not in end_nodes:
                end_nodes[event_node.event.name] = {}
            end_nodes[event_node.event.name][event_node.event.id] = event_node.nodes_idx

    print("Split XOR")
    # split xor operator
    for node in islice(epc["graph"], 0, len(epc["graph"]) - 1):
        node_name = node["data"]["label"]
        node_id = node["data"]["id"]
        node_variants = node["data"]["variants"]
        if node_name in start_nodes and node_id in start_nodes[node_name] and node_id in id_edges["in"]:
            edges_in = 0
            for edge in id_edges["in"][node_id]:
                edges_in += 1
                break
            if edges_in == 0:
                continue  # go to the next node

        if node_id not in id_edges["out"]:
            continue

        # the current node should have more than one out-edge for a split xor operator
        edges_out = len(id_edges["out"][node_id])
        if edges_out > 1:
            print("Insert split XOR")
            # the current node has at least one in-edge and more than one out-edge;
            # insert a xor operator between the current node and it's successors
            xor_node_id = f"{node_id}_XOR_SPLIT"

            # add the xor node to the graph
            epc["graph"].append(
                {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                          "variants": node_variants}})

            # add an edge between the current node and the xor node
            new_edge_start_xor = {"data": {"source": node_id, "target": xor_node_id, "label": "",
                                           "type": "DirectedEdge", "variants": node_variants}}
            edges.append(new_edge_start_xor)

            # remember an index of the inserted (current node -> xor)-edge in edges
            edges_idx_start_xor = len(edges) - 1

            # edges from xor node to successors of the current node
            id_edges["out"][xor_node_id] = {}
            for edges_idx, edge in id_edges["out"][node_id].items():
                target_node = edge["data"]["target"]
                new_edge_xor_startsucc = {
                    "data": {"source": xor_node_id, "target": target_node, "label": "",
                             "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                edges.append(new_edge_xor_startsucc)

                # remember an index of the inserted (xor -> current node succ)-edge in edges
                edges_idx_xor_startsucc = len(edges) - 1

                id_edges["out"][xor_node_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
                id_edges["in"][target_node][edges_idx_xor_startsucc] = new_edge_xor_startsucc

                # remove the old edge from the graph;
                # the old ones will be replaced with None so as not to disrupt indexing
                edges[edges_idx] = None

                # remove the old in-edges from the target node
                del id_edges["in"][target_node][edges_idx]

            # update in and out edge lists with the (current node -> xor)-edge
            id_edges["out"][node_id] = {}  # remove all the old edges
            id_edges["out"][node_id][edges_idx_start_xor] = new_edge_start_xor
            id_edges["in"][xor_node_id] = {}
            id_edges["in"][xor_node_id][edges_idx_start_xor] = new_edge_start_xor

    print("Join XOR")
    # join xor operator
    for node in islice(epc["graph"], 0, len(epc["graph"]) - 1):
        node_name = node["data"]["label"]
        node_id = node["data"]["id"]
        node_variants = node["data"]["variants"]
        if node_name in start_nodes and node_id in start_nodes[node_name] and node_id in id_edges["out"]:
            edges_out = 0
            for edge in id_edges["out"][node_id]:
                edges_out += 1
                break
            if edges_out == 0:
                continue  # go to the next node

        if node_id not in id_edges["in"]:
            continue

        # the current node should have more than one in-edge for a join xor operator
        edges_in = len(id_edges["in"][node_id])
        if edges_in > 1:
            print("Insert join XOR")
            # the current node has at least one in-edge and more than one out-edge;
            # insert a xor operator between the current node and it's predecessors
            xor_node_id = f"{node_id}_XOR_JOIN"

            # add the xor node to the graph
            epc["graph"].append(
                {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                          "variants": node_variants}})

            # add an edge between the current node and the xor node
            new_edge_xor_curnode = {"data": {"source": xor_node_id, "target": node_id, "label": "",
                                             "type": "DirectedEdge", "variants": node_variants}}
            edges.append(new_edge_xor_curnode)

            # remember an index of the inserted (xor -> current node)-edge in edges
            edges_idx_xor_curnode = len(edges) - 1

            # edges from predecessors of the current node to the xor node
            id_edges["in"][xor_node_id] = {}
            for edges_idx, edge in id_edges["in"][node_id].items():
                source_node = edge["data"]["source"]
                new_edge_curnodepred_xor = {
                    "data": {"source": source_node, "target": xor_node_id, "label": "",
                             "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                edges.append(new_edge_curnodepred_xor)

                # remember an index of the inserted (current node pred -> xor)-edge in edges
                edges_idx_curnodepred_xor = len(edges) - 1

                id_edges["in"][xor_node_id][edges_idx_curnodepred_xor] = new_edge_curnodepred_xor
                id_edges["out"][source_node][edges_idx_curnodepred_xor] = new_edge_curnodepred_xor

                # remove the old edge from the graph;
                # the old ones will be replaced with None so as not to disrupt indexing
                edges[edges_idx] = None

                # remove the old out-edge from the source node
                del id_edges["out"][source_node][edges_idx]

            # update in and out edge lists with the (xor -> current node)-edge
            id_edges["in"][node_id] = {}  # remove all the old edges
            id_edges["in"][node_id][edges_idx_xor_curnode] = new_edge_xor_curnode
            id_edges["out"][xor_node_id] = {}
            id_edges["out"][xor_node_id][edges_idx_xor_curnode] = new_edge_xor_curnode

    print("Start nodes split XOR")
    new_start_nodes = {}
    for start_node_name in start_nodes:
        if start_node_name not in new_start_nodes:
            new_start_nodes[start_node_name] = {}
        for node_id, nodes_idx in start_nodes[start_node_name].items():
            # if start node
            if node_id in id_edges["out"] and node_id in id_edges["in"] \
                    and len(id_edges["out"][node_id]) != 0 and len(id_edges["in"][node_id]) == 0:
                new_start_nodes[start_node_name][node_id] = nodes_idx

    start_nodes = new_start_nodes

    for start_node_name in start_nodes:
        if start_nodes[start_node_name]:  # if the dict of ids is not empty
            first_start_node_id = next(iter(start_nodes[start_node_name]))  # get one element from the dict
            xor_node_id = first_start_node_id

            if first_start_node_id in id_edges["out"]:
                # the start node should have more than one out-edge for a split xor operator
                edges_out = len(id_edges["out"][first_start_node_id])
                if edges_out > 1:
                    print("Insert start nodes split XOR")
                    # insert a xor operator between the start node and it's successors
                    xor_node_id = f"{first_start_node_id}_XOR_SPLIT"
                    start_node_variants = epc["graph"][start_nodes[start_node_name][first_start_node_id]]["data"][
                        "variants"]

                    # add the xor node to the graph
                    epc["graph"].append(
                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                  "variants": start_node_variants}})

                    # add an edge between the start node and the xor node
                    new_edge_start_xor = {
                        "data": {"source": first_start_node_id, "target": xor_node_id, "label": "",
                                 "type": "DirectedEdge", "variants": start_node_variants}}
                    edges.append(new_edge_start_xor)

                    # remember an index of the inserted (start node -> xor)-edge in edges
                    edges_idx_start_xor = len(edges) - 1

                    # edges from xor node to successors of the start node
                    id_edges["out"][xor_node_id] = {}
                    for edges_idx, edge in id_edges["out"][first_start_node_id].items():
                        target_node = edge["data"]["target"]
                        new_edge_xor_startsucc = {
                            "data": {"source": xor_node_id, "target": target_node, "label": "",
                                     "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                        edges.append(new_edge_xor_startsucc)

                        # remember an index of the inserted (xor -> start node succ)-edge in edges
                        edges_idx_xor_startsucc = len(edges) - 1

                        id_edges["out"][xor_node_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
                        id_edges["in"][target_node][edges_idx_xor_startsucc] = new_edge_xor_startsucc

                        # remove the old edge from the graph;
                        # the old ones will be replaced with None so as not to disrupt indexing
                        edges[edges_idx] = None

                        # remove the old in-edges from the target node
                        del id_edges["in"][target_node][edges_idx]

                    # update in and out edge lists with the (start node -> xor)-edge
                    id_edges["out"][first_start_node_id] = {}  # remove all the old edges
                    id_edges["out"][first_start_node_id][edges_idx_start_xor] = new_edge_start_xor
                    id_edges["in"][xor_node_id] = {}
                    id_edges["in"][xor_node_id][edges_idx_start_xor] = new_edge_start_xor

            pass_first = True  # the first start node was already processed
            for start_node_id in start_nodes[start_node_name]:
                if pass_first:
                    continue
                for edges_idx, edge in id_edges["out"][start_node_id].items():
                    target_node = edge["data"]["target"]
                    new_edge_xor_startsucc = {
                        "data": {"source": xor_node_id, "target": target_node, "label": "",
                                 "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                    edges.append(new_edge_xor_startsucc)

                    # remember an index of the inserted (xor -> start node succ)-edge in edges
                    edges_idx_xor_startsucc = len(edges) - 1

                    id_edges["out"][xor_node_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
                    id_edges["in"][target_node][edges_idx_xor_startsucc] = new_edge_xor_startsucc

                    # remove the old edge from the graph;
                    # the old ones will be replaced with None so as not to disrupt indexing
                    edges[edges_idx] = None

                    # remove the old in-edges from the target node
                    del id_edges["in"][target_node][edges_idx]

    print("End nodes join XOR")
    # the same for end nodes
    new_end_nodes = {}
    for end_node_name in end_nodes:
        if end_node_name not in new_end_nodes:
            new_end_nodes[end_node_name] = {}
        for node_id, nodes_idx in end_nodes[end_node_name].items():
            # if end node
            if node_id in id_edges["in"] and node_id in id_edges["out"] \
                    and len(id_edges["in"][node_id]) != 0 and len(id_edges["out"][node_id]) == 0:
                new_end_nodes[end_node_name][node_id] = nodes_idx

    end_nodes = new_end_nodes

    for end_node_name in end_nodes:
        if end_nodes[end_node_name]:  # if the dict of ids is not empty
            first_end_node_id = next(iter(end_nodes[end_node_name]))  # get one element from the dict
            xor_node_id = first_end_node_id

            if first_end_node_id in id_edges["in"]:
                # the current node should have more than one in-edge for a join xor operator
                edges_in = len(id_edges["in"][first_end_node_id])
                if edges_in > 1:
                    print("Insert end nodes join XOR")
                    # insert a xor operator between the end node and it's predecessors
                    xor_node_id = f"{first_end_node_id}_XOR_JOIN"
                    end_node_variants = epc["graph"][end_nodes[end_node_name][first_end_node_id]]["data"][
                        "variants"]

                    # add the xor node to the graph
                    epc["graph"].append(
                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                  "variants": end_node_variants}})

                    # add an edge between the end node and the xor node
                    new_edge_xor_end = {"data": {"source": xor_node_id, "target": first_end_node_id, "label": "",
                                                 "type": "DirectedEdge", "variants": end_node_variants}}
                    edges.append(new_edge_xor_end)

                    # remember an index of the inserted (xor -> end node)-edge in edges
                    edges_idx_xor_end = len(edges) - 1

                    # edges from predecessors of the end node to the xor node
                    id_edges["in"][xor_node_id] = {}
                    for edges_idx, edge in id_edges["in"][first_end_node_id].items():
                        source_node = edge["data"]["source"]
                        new_edge_endpred_xor = {
                            "data": {"source": source_node, "target": xor_node_id, "label": "",
                                     "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                        edges.append(new_edge_endpred_xor)

                        # remember an index of the inserted (end node pred -> xor)-edge in edges
                        edges_idx_endpred_xor = len(edges) - 1

                        id_edges["in"][xor_node_id][edges_idx_endpred_xor] = new_edge_endpred_xor
                        id_edges["out"][source_node][edges_idx_endpred_xor] = new_edge_endpred_xor

                        # remove the old edge from the graph;
                        # the old ones will be replaced with None so as not to disrupt indexing
                        edges[edges_idx] = None

                        # remove the old out-edge from the source node
                        del id_edges["out"][source_node][edges_idx]

                    # update in and out edge lists with the (xor -> end node)-edge
                    id_edges["in"][first_end_node_id] = {}  # remove all the old edges
                    id_edges["in"][first_end_node_id][edges_idx_xor_end] = new_edge_xor_end
                    id_edges["out"][xor_node_id] = {}
                    id_edges["out"][xor_node_id][edges_idx_xor_end] = new_edge_xor_end

            pass_first = True  # the first end node was already processed
            for end_node_id in end_nodes[end_node_name]:
                if pass_first:
                    continue
                for edges_idx, edge in id_edges["in"][end_node_id].items():
                    source_node = edge["data"]["source"]
                    new_edge_endpred_xor = {
                        "data": {"source": source_node, "target": xor_node_id, "label": "",
                                 "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                    edges.append(new_edge_endpred_xor)

                    # remember an index of the inserted (end node pred -> xor)-edge in edges
                    edges_idx_endpred_xor = len(edges) - 1

                    id_edges["in"][xor_node_id][edges_idx_endpred_xor] = new_edge_endpred_xor
                    id_edges["out"][source_node][edges_idx_endpred_xor] = new_edge_endpred_xor

                    # remove the old edge from the graph;
                    # the old ones will be replaced with None so as not to disrupt indexing
                    edges[edges_idx] = None

                    # remove the old out-edge from the source node
                    del id_edges["out"][source_node][edges_idx]

    print("Split AND")
    '''
    # join parallel events with AND-connector
    parallels = {}

    for node in epc["graph"]:
        node_id = node["data"]["id"]
        # remember all paths from a xor-split-node to a xor-join-node in parallels
        if "_XOR_SPLIT" in node_id:
            for edges_idx, edge in id_edges["out"][node_id].items():
                if "_XOR_" in edge["data"]["target"]:  # SPLIT or JOIN
                    continue
                else:
    '''

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
