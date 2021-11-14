from src.configs import configs as ct
from src.model import eventnode
from src.model.event import Event
from src.model.eventnode import EventNode


class EpcBuilder:

    def __init__(self, variants, functions):
        self.variants = variants
        self.functions = functions
        self.epc_dict = {}

    def create(self):
        epc = {"graph": []}
        start_nodes = {}
        end_nodes = {}
        events_by_name = {}
        event_ids = {}  # for event ids in cases

        # edges will be added at the end of the graph creation,
        # so that they are placed separate from the nodes in the back part of the pm["graph"] array
        edges = []
        # event id with their edges
        id_edges = {"in": {}, "out": {}}

        for idx, variant in enumerate(self.variants):  # FIXME DEBUG REMOVE IDX
            var_event_pred = None
            event_node = None
            already_there = False
            for idx, var_event in enumerate(variant.events):
                found_node = None
                already_there = False

                # find all event ids (for each case) of the current event for the current variant
                for case in variant.cases:
                    # the current event's index in the variant's list of events
                    # corresponds to the current event's index in the case's list of events
                    event_ids[case.id] = case.events[idx].id  # "case_0" : "event_id_0"

                if var_event.name in events_by_name:
                    for event_by_name in events_by_name[var_event.name]:
                        if not event_by_name.has_this_predecessor(var_event_pred):
                            if idx != len(variant.events) - 1:
                                # successor of the current var_event
                                var_event_succ = variant.events[idx + 1]
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
                            var_event_has_succ = idx != len(variant.events) - 1
                            if bool(event_by_name.successors) == var_event_has_succ and var_event_pred != event_by_name:
                                found_node = event_by_name
                                already_there = True
                                break

                if found_node is None:
                    new_e = Event(f"{variant.id}_{idx}_{var_event.name}", var_event.name)

                    epc["graph"].append(
                        {"data": {"id": new_e.id, "label": new_e.name, "type": "Event",
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

            # split xor operator
            for node in epc["graph"]:
                node_name = node["data"]["label"]
                node_id = node["data"]["id"]
                node_variants = node["data"]["variants"]
                if node_name in start_nodes and node_id in start_nodes[node_name]:
                    edges_in = 0
                    for edge in id_edges["in"][node_id]:
                        edges_in += 1
                        break
                    if edges_in == 0:
                        continue  # go to the next node

                # the current node should have more than one out-edge for a split xor operator
                edges_out = len(id_edges["out"][node_id])
                if edges_out > 1:
                    # the current node has at least one in-edge and more than one out-edge;
                    # insert a xor operator between the current node and it's successors
                    xor_node_id = f"{node_id}_XOR_SPLIT"

                    # add the xor node to the graph
                    epc["graph"].append(
                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                  "variants": node_variants}})

                    # add the edge between the current node and the xor node
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

            # join xor operator
            for node in epc["graph"]:
                node_name = node["data"]["label"]
                node_id = node["data"]["id"]
                node_variants = node["data"]["variants"]
                if node_name in start_nodes and node_id in start_nodes[node_name]:
                    edges_out = 0
                    for edge in id_edges["out"][node_id]:
                        edges_out += 1
                        break
                    if edges_out == 0:
                        continue  # go to the next node

                # the current node should have more than one in-edge for a join xor operator
                edges_in = len(id_edges["in"][node_id])
                if edges_in > 1:
                    # the current node has at least one in-edge and more than one out-edge;
                    # insert a xor operator between the current node and it's predecessors
                    xor_node_id = f"{node_id}_XOR_JOIN"

                    # add the xor node to the graph
                    epc["graph"].append(
                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                  "variants": node_variants}})

                    # add the edge between the current node and the xor node
                    new_edge_xor_curnode = {"data": {"source": xor_node_id, "target": node_id, "label": "",
                                                     "type": "DirectedEdge", "variants": node_variants}}
                    edges.append(new_edge_xor_curnode)

                    # remember an index of the inserted (current node -> xor)-edge in edges
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

        new_start_nodes = {}
        for start_node_name in start_nodes:
            if start_node_name not in new_start_nodes:
                new_start_nodes[start_node_name] = {}
            for node_id, nodes_idx in start_nodes[start_node_name].items():
                # if start node
                if len(id_edges["out"][node_id]) != 0 and len(id_edges["in"][node_id]) == 0:
                    new_start_nodes[start_node_name][node_id] = nodes_idx

        start_nodes = new_start_nodes

        for start_node_name in start_nodes:
            if start_nodes[start_node_name]:  # if the dict of ids is not empty
                first_start_node_id = next(iter(start_nodes[start_node_name]))  # get one element from the dict
                xor_node_id = first_start_node_id
                # the start node should have more than one out-edge for a split xor operator
                edges_out = len(id_edges["out"][first_start_node_id])
                if edges_out > 1:
                    # insert a xor operator between the start node and it's successors
                    xor_node_id = f"{first_start_node_id}_XOR_SPLIT"
                    start_node_variants = epc["graph"][start_nodes[start_node_name][first_start_node_id]]["data"][
                        "variants"]

                    # add the xor node to the graph
                    epc["graph"].append(
                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                  "variants": start_node_variants}})

                    # add the edge between the start node and the xor node
                    new_edge_start_xor = {"data": {"source": first_start_node_id, "target": xor_node_id, "label": "",
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

        # the same for end nodes
        new_end_nodes = {}
        for end_node_name in end_nodes:
            if end_node_name not in new_end_nodes:
                new_end_nodes[end_node_name] = {}
            for node_id, nodes_idx in end_nodes[end_node_name].items():
                # if end node
                if len(id_edges["in"][node_id]) != 0 and len(id_edges["out"][node_id]) == 0:
                    new_end_nodes[end_node_name][node_id] = nodes_idx

        end_nodes = new_end_nodes

        for end_node_name in end_nodes:
            if end_nodes[end_node_name]:  # if the dict of ids is not empty
                first_end_node_id = next(iter(end_nodes[end_node_name]))  # get one element from the dict
                xor_node_id = first_end_node_id
                # the current node should have more than one in-edge for a join xor operator
                edges_in = len(id_edges["in"][first_end_node_id])
                if edges_in > 1:
                    # insert a xor operator between the end node and it's predecessors
                    xor_node_id = f"{first_end_node_id}_XOR_JOIN"
                    end_node_variants = epc["graph"][end_nodes[end_node_name][first_end_node_id]]["data"][
                        "variants"]

                    # add the xor node to the graph
                    epc["graph"].append(
                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                  "variants": end_node_variants}})

                    # add the edge between the end node and the xor node
                    new_edge_xor_end = {"data": {"source": xor_node_id, "target": first_end_node_id, "label": "",
                                                     "type": "DirectedEdge", "variants": end_node_variants}}
                    edges.append(new_edge_xor_end)

                    # remember an index of the inserted (end node -> xor)-edge in edges
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

        for edge in edges:
            if edge is not None:
                epc["graph"].append(edge)

        print("graph created")

        self.epc_dict = epc
