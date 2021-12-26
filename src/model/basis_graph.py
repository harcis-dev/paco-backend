import math
from itertools import islice

from src.configs.configs import EpcLabels
from src.model.event import Event
from src.model.eventnode import EventNode
from src.model.parallel_activity import ParallelActivity


class BasisGraph:
    def __init__(self):
        self.graph = {"graph": []}
        self.start_nodes = {}
        self.end_nodes = {}
        self.events_by_name = {}
        # event id and its index in the graph dictionary
        # to have access to all event attributes by an id
        self.events_by_index = {}

        # edges will be added at the end of the graph creation,
        # so that they are placed separate from the nodes in the back part of the pm["graph"] array
        self.edges = []
        # event ids with its edges
        self.id_edges = {"in": {}, "out": {}}

    def create_basis_graph(self, variants):
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
                    # DEBUG
                    # if var_event.id.split("_")[0] != case.events[event_idx].id.split("_")[0]:
                    #     print(f"{var_event.id.split('_')[0]} vs {case.events[event_idx].id.split('_')[0]}")
                    #     print(f"variant events: {variant.events}")
                    #     print(f"case events: {case.events}")
                    #     raise

                if var_event.name in self.events_by_name:
                    for event_by_name in self.events_by_name[var_event.name]:
                        if not event_by_name.has_this_predecessor(var_event_pred):
                            if event_idx != len(variant.events) - 1:
                                # successor of the current var_event
                                var_event_succ = variant.events[event_idx + 1]
                                if var_event_succ.name in self.events_by_name:
                                    for event_succ_by_name in self.events_by_name[var_event_succ.name]:
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

                    self.graph["graph"].append(
                        {"data": {"id": new_e.id, "label": new_e.name, "type": "node",
                                  "variants": {variant.id: event_ids}}})
                    # remember an index of the inserted node
                    node_idx = len(self.graph["graph"]) - 1
                    self.events_by_index[new_e.id] = node_idx

                    if new_e.name not in self.events_by_name:
                        self.events_by_name[new_e.name] = []

                    found_node = EventNode(new_e, node_idx)
                    self.events_by_name[new_e.name].append(found_node)
                    print(f"new foundEvent: {found_node.event.id}")
                else:
                    self.graph["graph"][found_node.node_idx]["data"]["variants"][variant.id] = event_ids
                    print(f"foundEvent: {found_node.event.id}")

                event_node = found_node
                if var_event_pred is not None:
                    var_event_pred.successors.append(event_node)
                    event_node.predecessors.append(var_event_pred)

                    # searching for an edge only if the event was found/is already in the graph
                    found_edge = False
                    for edge in self.edges:
                        if edge["data"]["source"] == var_event_pred.event.id and \
                                edge["data"]["target"] == event_node.event.id:
                            # add the current variant to the map of variants of the edge
                            edge["data"]["variants"][variant.id] = event_ids
                            found_edge = True
                            break

                    if not found_edge:
                        new_edge = {
                            "data": {"source": var_event_pred.event.id, "target": event_node.event.id, "label": "",
                                     "type": "DirectedEdge", "variants": {variant.id: event_ids}}}
                        self.edges.append(new_edge)

                        # remember an index of the inserted edge in edges
                        edge_idx = len(self.edges) - 1

                        if event_node.event.id not in self.id_edges["in"]:
                            self.id_edges["in"][event_node.event.id] = {}
                        self.id_edges["in"][event_node.event.id][edge_idx] = new_edge

                        if var_event_pred.event.id not in self.id_edges["out"]:
                            self.id_edges["out"][var_event_pred.event.id] = {}
                        self.id_edges["out"][var_event_pred.event.id][edge_idx] = new_edge

                elif not already_there:
                    if var_event.name not in self.start_nodes:
                        self.start_nodes[var_event.name] = {}
                    self.start_nodes[var_event.name][event_node.event.id] = event_node.node_idx

                var_event_pred = event_node

            if not already_there:
                if event_node.event.name not in self.end_nodes:
                    self.end_nodes[event_node.event.name] = {}
                self.end_nodes[event_node.event.name][event_node.event.id] = event_node.node_idx

        print("Split XOR")
        # split xor operator
        for node in islice(self.graph["graph"], 0, len(self.graph["graph"]) - 1):
            node_name = node["data"]["label"]
            node_id = node["data"]["id"]
            node_variants = node["data"]["variants"]
            if node_name in self.start_nodes and node_id in self.start_nodes[node_name] and node_id in self.id_edges[
                "in"]:
                edges_in = 0
                for edge in self.id_edges["in"][node_id]:
                    edges_in += 1
                    break
                if edges_in == 0:
                    continue  # go to the next node

            if node_id not in self.id_edges["out"]:
                continue

            # the current node should have more than one out-edge for a split xor operator
            edges_out = len(self.id_edges["out"][node_id])
            if edges_out > 1:
                print("Insert split XOR")
                # the current node has at least one in-edge and more than one out-edge;
                # insert a xor operator between the current node and it's successors
                xor_node_id = f"{node_id}_XOR_SPLIT"

                # add the xor node to the graph
                self.graph["graph"].append(
                    {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                              "variants": node_variants}})
                self.events_by_index[xor_node_id] = len(self.graph["graph"]) - 1

                # add an edge between the current node and the xor node
                new_edge_start_xor = {"data": {"source": node_id, "target": xor_node_id, "label": "",
                                               "type": "DirectedEdge", "variants": node_variants}}
                self.edges.append(new_edge_start_xor)

                # remember an index of the inserted (current node -> xor)-edge in edges
                edge_idx_start_xor = len(self.edges) - 1

                # edges from xor node to successors of the current node
                self.id_edges["out"][xor_node_id] = {}
                for edge_idx, edge in self.id_edges["out"][node_id].items():
                    target_node = edge["data"]["target"]
                    new_edge_xor_startsucc = {
                        "data": {"source": xor_node_id, "target": target_node, "label": "",
                                 "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                    self.edges.append(new_edge_xor_startsucc)

                    # remember an index of the inserted (xor -> current node succ)-edge in edges
                    edge_idx_xor_startsucc = len(self.edges) - 1

                    self.id_edges["out"][xor_node_id][edge_idx_xor_startsucc] = new_edge_xor_startsucc
                    self.id_edges["in"][target_node][edge_idx_xor_startsucc] = new_edge_xor_startsucc

                    # remove the old edge from the graph;
                    # the old ones will be replaced with None so as not to disrupt indexing
                    self.edges[edge_idx] = None

                    # remove the old in-edges from the target node
                    del self.id_edges["in"][target_node][edge_idx]

                # update in and out edge lists with the (current node -> xor)-edge
                self.id_edges["out"][node_id] = {}  # remove all the old edges
                self.id_edges["out"][node_id][edge_idx_start_xor] = new_edge_start_xor
                self.id_edges["in"][xor_node_id] = {}
                self.id_edges["in"][xor_node_id][edge_idx_start_xor] = new_edge_start_xor

        print("Join XOR")
        # join xor operator
        for node in islice(self.graph["graph"], 0, len(self.graph["graph"]) - 1):
            node_name = node["data"]["label"]
            node_id = node["data"]["id"]
            node_variants = node["data"]["variants"]
            if node_name in self.start_nodes and node_id in self.start_nodes[node_name] and node_id in self.id_edges[
                "out"]:
                edges_out = 0
                for edge in self.id_edges["out"][node_id]:
                    edges_out += 1
                    break
                if edges_out == 0:
                    continue  # go to the next node

            if node_id not in self.id_edges["in"]:
                continue

            # the current node should have more than one in-edge for a join xor operator
            edges_in = len(self.id_edges["in"][node_id])
            if edges_in > 1:
                print("Insert join XOR")
                # the current node has at least one in-edge and more than one out-edge;
                # insert a xor operator between the current node and it's predecessors
                xor_node_id = f"{node_id}_XOR_JOIN"

                # add the xor node to the graph
                self.graph["graph"].append(
                    {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                              "variants": node_variants}})
                self.events_by_index[xor_node_id] = len(self.graph["graph"]) - 1

                # add an edge between the current node and the xor node
                new_edge_xor_curnode = {"data": {"source": xor_node_id, "target": node_id, "label": "",
                                                 "type": "DirectedEdge", "variants": node_variants}}
                self.edges.append(new_edge_xor_curnode)

                # remember an index of the inserted (xor -> current node)-edge in self.edges
                edge_idx_xor_curnode = len(self.edges) - 1

                # self.edges from predecessors of the current node to the xor node
                self.id_edges["in"][xor_node_id] = {}
                for edge_idx, edge in self.id_edges["in"][node_id].items():
                    source_node = edge["data"]["source"]
                    new_edge_curnodepred_xor = {
                        "data": {"source": source_node, "target": xor_node_id, "label": "",
                                 "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                    self.edges.append(new_edge_curnodepred_xor)

                    # remember an index of the inserted (current node pred -> xor)-edge in self.edges
                    edge_idx_curnodepred_xor = len(self.edges) - 1

                    self.id_edges["in"][xor_node_id][edge_idx_curnodepred_xor] = new_edge_curnodepred_xor
                    self.id_edges["out"][source_node][edge_idx_curnodepred_xor] = new_edge_curnodepred_xor

                    # remove the old edge from the graph;
                    # the old ones will be replaced with None so as not to disrupt indexing
                    self.edges[edge_idx] = None

                    # remove the old out-edge from the source node
                    del self.id_edges["out"][source_node][edge_idx]

                # update in and out edge lists with the (xor -> current node)-edge
                self.id_edges["in"][node_id] = {}  # remove all the old self.edges
                self.id_edges["in"][node_id][edge_idx_xor_curnode] = new_edge_xor_curnode
                self.id_edges["out"][xor_node_id] = {}
                self.id_edges["out"][xor_node_id][edge_idx_xor_curnode] = new_edge_xor_curnode

        print("Start nodes split XOR")
        new_start_nodes = {}
        for start_node_name in self.start_nodes:
            if start_node_name not in new_start_nodes:
                new_start_nodes[start_node_name] = {}
            for node_id, node_idx in self.start_nodes[start_node_name].items():
                # if start node
                if node_id in self.id_edges["out"] and node_id in self.id_edges["in"] \
                        and len(self.id_edges["out"][node_id]) != 0 and len(self.id_edges["in"][node_id]) == 0:
                    new_start_nodes[start_node_name][node_id] = node_idx

        self.start_nodes = new_start_nodes

        for start_node_name in self.start_nodes:
            if self.start_nodes[start_node_name]:  # if the dict of ids is not empty
                first_start_node_id = next(iter(self.start_nodes[start_node_name]))  # get one element from the dict
                xor_node_id = first_start_node_id

                if first_start_node_id in self.id_edges["out"]:
                    # the start node should have more than one out-edge for a split xor operator
                    edges_out = len(self.id_edges["out"][first_start_node_id])
                    if edges_out > 1:
                        print("Insert start nodes split XOR")
                        # insert a xor operator between the start node and it's successors
                        xor_node_id = f"{first_start_node_id}_XOR_SPLIT"
                        start_node_variants = \
                            self.graph["graph"][self.start_nodes[start_node_name][first_start_node_id]]["data"][
                                "variants"]

                        # add the xor node to the graph
                        self.graph["graph"].append(
                            {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                      "variants": start_node_variants}})
                        self.events_by_index[xor_node_id] = len(self.graph["graph"]) - 1

                        # add an edge between the start node and the xor node
                        new_edge_start_xor = {
                            "data": {"source": first_start_node_id, "target": xor_node_id, "label": "",
                                     "type": "DirectedEdge", "variants": start_node_variants}}
                        self.edges.append(new_edge_start_xor)

                        # remember an index of the inserted (start node -> xor)-edge in edges
                        edge_idx_start_xor = len(self.edges) - 1

                        # edges from xor node to successors of the start node
                        self.id_edges["out"][xor_node_id] = {}
                        for edge_idx, edge in self.id_edges["out"][first_start_node_id].items():
                            target_node = edge["data"]["target"]
                            new_edge_xor_startsucc = {
                                "data": {"source": xor_node_id, "target": target_node, "label": "",
                                         "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                            self.edges.append(new_edge_xor_startsucc)

                            # remember an index of the inserted (xor -> start node succ)-edge in edges
                            edge_idx_xor_startsucc = len(self.edges) - 1

                            self.id_edges["out"][xor_node_id][edge_idx_xor_startsucc] = new_edge_xor_startsucc
                            self.id_edges["in"][target_node][edge_idx_xor_startsucc] = new_edge_xor_startsucc

                            # remove the old edge from the graph;
                            # the old ones will be replaced with None so as not to disrupt indexing
                            self.edges[edge_idx] = None

                            # remove the old in-edges from the target node
                            del self.id_edges["in"][target_node][edge_idx]

                        # update in and out edge lists with the (start node -> xor)-edge
                        self.id_edges["out"][first_start_node_id] = {}  # remove all the old edges
                        self.id_edges["out"][first_start_node_id][edge_idx_start_xor] = new_edge_start_xor
                        self.id_edges["in"][xor_node_id] = {}
                        self.id_edges["in"][xor_node_id][edge_idx_start_xor] = new_edge_start_xor

                pass_first = True  # the first start node was already processed
                for start_node_id in self.start_nodes[start_node_name]:
                    if pass_first:
                        continue
                    for edge_idx, edge in self.id_edges["out"][start_node_id].items():
                        target_node = edge["data"]["target"]
                        new_edge_xor_startsucc = {
                            "data": {"source": xor_node_id, "target": target_node, "label": "",
                                     "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                        self.edges.append(new_edge_xor_startsucc)

                        # remember an index of the inserted (xor -> start node succ)-edge in edges
                        edge_idx_xor_startsucc = len(self.edges) - 1

                        self.id_edges["out"][xor_node_id][edge_idx_xor_startsucc] = new_edge_xor_startsucc
                        self.id_edges["in"][target_node][edge_idx_xor_startsucc] = new_edge_xor_startsucc

                        # remove the old edge from the graph;
                        # the old ones will be replaced with None so as not to disrupt indexing
                        self.edges[edge_idx] = None

                        # remove the old in-edges from the target node
                        del self.id_edges["in"][target_node][edge_idx]

        print("End nodes join XOR")
        # the same for end nodes
        new_end_nodes = {}
        for end_node_name in self.end_nodes:
            if end_node_name not in new_end_nodes:
                new_end_nodes[end_node_name] = {}
            for node_id, node_idx in self.end_nodes[end_node_name].items():
                # if end node
                if node_id in self.id_edges["in"] and node_id in self.id_edges["out"] \
                        and len(self.id_edges["in"][node_id]) != 0 and len(self.id_edges["out"][node_id]) == 0:
                    new_end_nodes[end_node_name][node_id] = node_idx

        end_nodes = new_end_nodes

        for end_node_name in end_nodes:
            if end_nodes[end_node_name]:  # if the dict of ids is not empty
                first_end_node_id = next(iter(end_nodes[end_node_name]))  # get one element from the dict
                xor_node_id = first_end_node_id

                if first_end_node_id in self.id_edges["in"]:
                    # the current node should have more than one in-edge for a join xor operator
                    edges_in = len(self.id_edges["in"][first_end_node_id])
                    if edges_in > 1:
                        print("Insert end nodes join XOR")
                        # insert a xor operator between the end node and it's predecessors
                        xor_node_id = f"{first_end_node_id}_XOR_JOIN"
                        end_node_variants = self.graph["graph"][end_nodes[end_node_name][first_end_node_id]]["data"][
                            "variants"]

                        # add the xor node to the graph
                        self.graph["graph"].append(
                            {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                      "variants": end_node_variants}})
                        self.events_by_index[xor_node_id] = len(self.graph["graph"]) - 1

                        # add an edge between the end node and the xor node
                        new_edge_xor_end = {"data": {"source": xor_node_id, "target": first_end_node_id, "label": "",
                                                     "type": "DirectedEdge", "variants": end_node_variants}}
                        self.edges.append(new_edge_xor_end)

                        # remember an index of the inserted (xor -> end node)-edge in edges
                        edge_idx_xor_end = len(self.edges) - 1

                        # edges from predecessors of the end node to the xor node
                        self.id_edges["in"][xor_node_id] = {}
                        for edge_idx, edge in self.id_edges["in"][first_end_node_id].items():
                            source_node = edge["data"]["source"]
                            new_edge_endpred_xor = {
                                "data": {"source": source_node, "target": xor_node_id, "label": "",
                                         "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                            self.edges.append(new_edge_endpred_xor)

                            # remember an index of the inserted (end node pred -> xor)-edge in edges
                            edge_idx_endpred_xor = len(self.edges) - 1

                            self.id_edges["in"][xor_node_id][edge_idx_endpred_xor] = new_edge_endpred_xor
                            self.id_edges["out"][source_node][edge_idx_endpred_xor] = new_edge_endpred_xor

                            # remove the old edge from the graph;
                            # the old ones will be replaced with None so as not to disrupt indexing
                            self.edges[edge_idx] = None

                            # remove the old out-edge from the source node
                            del self.id_edges["out"][source_node][edge_idx]

                        # update in and out edge lists with the (xor -> end node)-edge
                        self.id_edges["in"][first_end_node_id] = {}  # remove all the old edges
                        self.id_edges["in"][first_end_node_id][edge_idx_xor_end] = new_edge_xor_end
                        self.id_edges["out"][xor_node_id] = {}
                        self.id_edges["out"][xor_node_id][edge_idx_xor_end] = new_edge_xor_end

                pass_first = True  # the first end node was already processed
                for end_node_id in end_nodes[end_node_name]:
                    if pass_first:
                        continue
                    for edge_idx, edge in self.id_edges["in"][end_node_id].items():
                        source_node = edge["data"]["source"]
                        new_edge_endpred_xor = {
                            "data": {"source": source_node, "target": xor_node_id, "label": "",
                                     "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                        self.edges.append(new_edge_endpred_xor)

                        # remember an index of the inserted (end node pred -> xor)-edge in edges
                        edge_idx_endpred_xor = len(self.edges) - 1

                        self.id_edges["in"][xor_node_id][edge_idx_endpred_xor] = new_edge_endpred_xor
                        self.id_edges["out"][source_node][edge_idx_endpred_xor] = new_edge_endpred_xor

                        # remove the old edge from the graph;
                        # the old ones will be replaced with None so as not to disrupt indexing
                        self.edges[edge_idx] = None

                        # remove the old out-edge from the source node
                        del self.id_edges["out"][source_node][edge_idx]

        print("Split AND")

        # join parallel activities (paths of events) with AND-connector
        parallels = {}

        for node_idx, node in enumerate(self.graph["graph"]):
            node_id = node["data"]["id"]
            # remember in parallels all paths from a xor-split-node to a xor-join-node
            if "_XOR_SPLIT" in node_id:  # if the node is a split xor operator
                # find all paths for every successor node of split xor to the nearest join xor (if exists)
                for edge_idx, edge in self.id_edges["out"][node_id].items():
                    # if the edge leads to another XOR-node, i.e. XOR -> XOR
                    if "_XOR_" in edge["data"]["target"]:  # SPLIT or JOIN
                        continue
                    else:
                        pa = ParallelActivity()
                        pa.set_start_gateway(node_idx, len(self.id_edges["out"][node_id]))
                        self.find_parallels(node_id, pa)

                        # no join xor found
                        if pa.end_gateway_idx == -1: continue

                        # create an activity footprint as sorted array of events of an activity and gateway label
                        # so identical paths have the same footprint, regardless of the event order,
                        # if they flow into the same xor node.
                        pa.labels_path.sort()
                        # parallel activities should have the same join xor
                        pa.labels_path.append(self.graph["graph"][pa.end_gateway_idx]["data"]["id"])
                        footprint = tuple(pa.labels_path)

                        if footprint not in parallels:
                            parallels[footprint] = []

                        # check if an equal activity (with the same events order, not sorted) is already in parallels
                        already_there = False
                        for parallels_pa in parallels[footprint]:
                            if parallels_pa.labels_path == pa.labels_path:
                                already_there = True

                        if not already_there:
                            parallels[footprint].append(pa)

        # check if parallelism of activities present in parallels
        # for every footprint
        for fp, fp_pas in parallels.items():
            # number of events in the footprint activity
            size = len(fp_pas[0])
            # if more than one event then parallelism possible
            if size > 1:
                '''
                Condition for parallelism:
                there must be all possible paths, i.e. combinations of the activities,
                between the split and join xor operators. As equal combination are possible,
                they should be handled right -- only one of them will be taken into account.
                In general, it means that the #paths must be equal to the result of the
                factorial of #activities divided by the product of factorials of activity frequencies.
                
                Example:
                (XOR_SPLIT) -> (A) -> (A) -> (B) -> (XOR_JOIN)
                (XOR_SPLIT) -> (B) -> (A) -> (A) -> (XOR_JOIN)
                (XOR_SPLIT) -> (A) -> (B) -> (A) -> (XOR_JOIN)
                In this case, the parallelism is present, since
                fac(3) / (fac(2) * fac(1)) = 3
                
                Thr result would be as follows:
                (AND_SPLIT) -> (A) -> (AND_JOIN)
                (AND_SPLIT) -> (B) -> (AND_JOIN)
                '''

                # count the frequency for one of footprint activities, as it's equal for all identical activities
                denom = 1
                for event_count in fp_pas[0].event_count.values():
                    denom *= math.factorial(event_count)
                combin_count = math.factorial(size) / denom

                # if parallelism present,
                # the graph can be modified
                if combin_count == len(fp_pas):
                    # contains a name of every unique event label for each activity
                    # with its index in the graph dict;
                    # each (unique) node will be added to unique_events
                    # and then newly attached to the graph as a replacement for the removed one(s)
                    unique_events = {}
                    # for every parallel activity with the same footprint
                    for pa in fp_pas:
                        # for every event of the activity
                        for path_idx, node_label in enumerate(pa.labels_path):
                            # Same indices in nodes and labels paths reference same events
                            node_idx = pa.nodes_path[path_idx]
                            node_id = self.graph["graph"][node_idx]["data"]["id"]
                            # if the node_id contains "XOR_SPLIT", then it is a block
                            is_block = "_XOR_SPLIT" in node_label
                            # old nodes on the path from split to join xor will be removed;
                            # at first add unique events to unique_events
                            if node_label not in unique_events:
                                unique_events[node_label] = node_idx
                            else:
                                # if found, then merge variants of the current event/block
                                # with the ones of the identical event/block in unique_events;
                                # the event/block in unique_events is thus a representative
                                # of all nodes/blocks with an equal label

                                if is_block:
                                    self.deep_merge_two_block(unique_events[node_label], node_idx)
                                else:
                                    deep_merge_two_dicts(
                                        self.graph["graph"][unique_events[node_label]]["data"]["variants"],
                                        self.graph["graph"][node_idx]["data"]["variants"])

                                # remove the old node from the graph;
                                # the old ones will be replaced with None so as not to disrupt indexing
                                self.graph["graph"][node_idx] = None
                                del self.events_by_index[node_idx]

                            # remove in and out edges to the old node/block
                            if is_block:
                                self.remove_edges_block(node_id, pa.block_start_end[node_id])
                            else:
                                self.remove_edges_event(node_id)

                    # add the ADD split node
                    xor_node_id = self.graph["graph"][fp_pas[0].start_gateway_idx]["data"]["id"]
                    and_node_id = xor_node_id.replace("XOR", "AND")
                    and_node_label = "∧"
                    and_node_type = "AND"
                    and_node_variants = {}
                    # if the split XOR serves as a gateway for parallel activities only,
                    # then convert this to an AND operator
                    if fp_pas[0].outgoing_edges_count == len(fp_pas):
                        # self.graph["graph"][fp_pas[0].start_gateway_idx]["data"]["id"] = and_node_id -> then should be changed in all edges
                        self.graph["graph"][fp_pas[0].start_gateway_idx]["data"]["label"] = and_node_label
                        self.graph["graph"][fp_pas[0].start_gateway_idx]["data"][
                            "type"] = and_node_type  # the number of variants remains the same
                        for unique_node_idx in unique_events.values():
                            node_id = self.graph["graph"][unique_node_idx]["data"]["id"]
                            node_variants = self.graph["graph"][unique_node_idx]["data"]["variants"]
                            new_edge_and_unique_event = {
                                "data": {"source": and_node_id, "target": node_id, "label": "",
                                         "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_and_unique_event)
                            edge_idx_and_unique_event = len(self.edges) - 1
                            self.id_edges["in"][node_id][edge_idx_and_unique_event] = new_edge_and_unique_event
                            self.id_edges["out"][and_node_id][edge_idx_and_unique_event] = new_edge_and_unique_event
                    else:  # parallel activities are not the only successors of the split XOR
                        # insert a split AND operator between the split XOR and the parallel activities
                        print("Insert AND split")

                        # as the split AND operator contains all variants of its successors,
                        # all the unique_event variants will be merged and assigned to it
                        ue_iter = iter(unique_events)
                        node_variants = self.graph["graph"][unique_events[next(ue_iter)]]["data"]["variants"]
                        and_node_variants = node_variants.copy()
                        while True:
                            try:
                                node_variants = self.graph["graph"][unique_events[next(ue_iter)]]["data"]["variants"]
                                deep_merge_two_dicts(and_node_variants, node_variants)
                            except StopIteration:
                                break

                        # add the AND node to the graph
                        self.graph["graph"].append(
                            {"data": {"id": and_node_id, "label": and_node_label, "type": and_node_type,
                                      "variants": and_node_variants}})
                        self.events_by_index[and_node_id] = len(self.graph["graph"]) - 1

                        # add an edge XOR -> AND
                        new_edge_xor_and = {"data": {"source": xor_node_id, "target": and_node_id, "label": "",
                                                     "type": "DirectedEdge", "variants": and_node_variants}}
                        self.edges.append(new_edge_xor_and)
                        edge_idx_xor_and = len(self.edges) - 1
                        self.id_edges["in"][and_node_id][edge_idx_xor_and] = new_edge_xor_and
                        self.id_edges["out"][xor_node_id][edge_idx_xor_and] = new_edge_xor_and

                        # add a new edge from the AND node to every unique event node
                        for unique_node_idx in unique_events.values():
                            node_id = self.graph["graph"][unique_node_idx]["data"]["id"]
                            node_variants = self.graph["graph"][unique_node_idx]["data"]["variants"]
                            new_edge_and_unique_event = {
                                "data": {"source": and_node_id, "target": node_id, "label": "",
                                         "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_and_unique_event)
                            edge_idx_and_unique_event = len(self.edges) - 1
                            self.id_edges["in"][node_id][edge_idx_and_unique_event] = new_edge_and_unique_event
                            self.id_edges["out"][and_node_id][edge_idx_and_unique_event] = new_edge_and_unique_event

                    # add the AND join node
                    xor_node_id = self.graph["graph"][fp_pas[0].end_gateway_idx]["data"]["id"]
                    and_node_id = xor_node_id.replace("XOR", "AND")
                    and_node_label = "∧"
                    and_node_type = "AND"
                    # if into the join XOR flow parallel activities only,
                    # then convert it to an AND operator
                    if fp_pas[0].incoming_edges_count == len(fp_pas):
                        self.graph["graph"][fp_pas[0].end_gateway_idx]["data"]["label"] = and_node_label
                        self.graph["graph"][fp_pas[0].end_gateway_idx]["data"][
                            "type"] = and_node_type
                        for unique_node_idx in unique_events.values():
                            node_id = self.graph["graph"][unique_node_idx]["data"]["id"]
                            node_variants = self.graph["graph"][unique_node_idx]["data"]["variants"]
                            new_edge_unique_event_and = {
                                "data": {"source": node_id, "target": and_node_id, "label": "",
                                         "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_unique_event_and)
                            edge_idx_unique_event_and = len(self.edges) - 1
                            self.id_edges["in"][and_node_id][edge_idx_unique_event_and] = new_edge_unique_event_and
                            self.id_edges["out"][node_id][edge_idx_unique_event_and] = new_edge_unique_event_and
                    else:  # parallel activities are not the only predecessors of the join XOR
                        # insert a join AND operator between the parallel activities and the join XOR
                        print("Insert AND join")

                        # as the join AND operator contains all variants of its predecessors,
                        # all the unique_event variants should be merged and assigned to it;
                        # but this information is already present in the split AND
                        # and can be reused, if a split AND operator was inserted.
                        if not and_node_variants:  # if empty / split AND was not inserted
                            ue_iter = iter(unique_events)
                            node_variants = self.graph["graph"][unique_events[next(ue_iter)]]["data"]["variants"]
                            and_node_variants = node_variants.copy()
                            while True:
                                try:
                                    node_variants = self.graph["graph"][unique_events[next(ue_iter)]]["data"]["variants"]
                                    deep_merge_two_dicts(and_node_variants, node_variants)
                                except StopIteration:
                                    break

                        # add the AND node to the graph
                        self.graph["graph"].append(
                            {"data": {"id": and_node_id, "label": and_node_label, "type": and_node_type,
                                      "variants": and_node_variants}})
                        self.events_by_index[and_node_id] = len(self.graph["graph"]) - 1

                        # add an edge AND -> XOR
                        new_edge_and_xor = {"data": {"source": and_node_id, "target": xor_node_id, "label": "",
                                                     "type": "DirectedEdge", "variants": and_node_variants}}
                        self.edges.append(new_edge_and_xor)
                        edge_idx_and_xor = len(self.edges) - 1
                        self.id_edges["in"][xor_node_id][edge_idx_and_xor] = new_edge_and_xor
                        self.id_edges["out"][and_node_id][edge_idx_and_xor] = new_edge_and_xor

                        # add a new edge from every unique event node to the AND node
                        for unique_node_idx in unique_events.values():
                            node_id = self.graph["graph"][unique_node_idx]["data"]["id"]
                            node_variants = self.graph["graph"][unique_node_idx]["data"]["variants"]
                            new_edge_unique_event_and = {
                                "data": {"source": node_id, "target": and_node_id, "label": "",
                                         "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_unique_event_and)
                            edge_idx_unique_event_and = len(self.edges) - 1
                            self.id_edges["in"][and_node_id][edge_idx_unique_event_and] = new_edge_unique_event_and
                            self.id_edges["out"][node_id][edge_idx_unique_event_and] = new_edge_unique_event_and

        print("removing None values")
        temp = []
        for node in self.graph["graph"]:
            if node is not None:
                temp.append(node)
        self.graph["graph"] = temp

        for edge in self.edges:
            if edge is not None:
                #print(f'{edge["data"]["source"]} -> {edge["data"]["target"]}')
                self.graph["graph"].append(edge)

        print("graph created")

    '''
        Iterative Depth First Search as basis
        of parallel activity elimination.
    '''

    def find_parallels(self, node_id, pa):
        # create a stack for dfs
        stack = []

        # a node cannot be revisited in this type of graph:
        # if two or more paths lead to the same node,
        # then this node is an operator (in this case xor).

        # push the current source node
        stack.append(node_id)
        edges_in = self.id_edges["in"]
        edges_out = self.id_edges["out"]

        while len(stack):
            # next node
            node_id = stack.pop()
            node_idx = self.events_by_index[node_id]

            if "_XOR_JOIN" in node_id:
                pa.set_end_gateway(node_idx, len(edges_in[node_id]))
                break

            if "_XOR_SPLIT" in node_id:
                # node_id is now a join xor of the block or a graph leaf
                join_xor_id, node_label = self.add_block(node_id, pa)
                # node_id is split xor
                pa.block_start_end[node_id] = join_xor_id
                node_id = join_xor_id
            else:
                node_label = self.graph["graph"][node_idx]["data"]["label"]

            # add an event label or a block footprint to the parallel activity
            pa.add_event(node_idx, node_label)

            if node_id in edges_out:
                for edge_idx, edge in edges_out[node_id].items():
                    stack.append(edge["data"]["target"])

    '''
        pa blocks: [{E: [E, D], J: [J, {H: [H,...], F: {F, G}}]}]
    '''

    def add_block(self, split_xor_id, pa):
        block = {}
        edges_out = self.id_edges["out"]
        join_xor_id = None

        for edge_idx, edge in edges_out[split_xor_id].items():
            xor_succ_id = edge["data"]["target"]  # xor successor (cannot be another xor)
            xor_succ_label = self.get_label_by_id(xor_succ_id)
            # remember the first node of every xor branch to sort the block
            block[xor_succ_label] = [xor_succ_label]
            cur_succ_id = xor_succ_id
            while cur_succ_id in self.id_edges["out"]:
                # there is only one successor possible ([0])
                cur_succ_id = edges_out[cur_succ_id][0]["data"]["target"]
                nested_block = None

                if "_XOR_JOIN" in cur_succ_id:
                    join_xor_id = cur_succ_id
                    break

                # a nested block
                if "_XOR_SPLIT" in cur_succ_id:
                    cur_succ_id, nested_block = self.add_block(cur_succ_id, pa)

                if nested_block is None:  # node, not a block
                    block[xor_succ_label].append(self.get_label_by_id(cur_succ_id))
                else:  # block, not a node
                    # store a block footprint as its label
                    block[xor_succ_label].append(str(dict(sorted(nested_block.items()))))

        if join_xor_id is not None:
            return join_xor_id, block
        return cur_succ_id, block  # join xor or a graph leaf

    '''
        Removes all edges (in and out) from the edges dict for a node id
    '''

    def remove_edges_event(self, event_id):
        self.remove_edges(event_id, "in")
        self.remove_edges(event_id, "out")

    def remove_edges_block(self, block_start_id, block_end_id):
        self.remove_edges(block_start_id, "in")
        self.remove_edges(block_end_id, "out")

    def remove_edges(self, node_id, direction):
        if node_id in self.id_edges[direction]:
            edges_out_to_remove = self.id_edges[direction][node_id]
            for edge_idx_to_remove in edges_out_to_remove:
                self.edges[edge_idx_to_remove] = None
                del self.id_edges[direction][node_id][edge_idx_to_remove]

    def get_label_by_id(self, node_id):
        node_idx = self.events_by_index[node_id]
        return self.graph["graph"][node_idx]["data"]["label"]

    def deep_merge_two_block(self, this_block_xor_idx, other_block_xor_idx):
        # merge split xor operators of the two block
        deep_merge_two_dicts(
            self.graph["graph"][this_block_xor_idx]["data"]["variants"],
            self.graph["graph"][other_block_xor_idx]["data"]["variants"])
        this_block_xor_id = self.graph["graph"][this_block_xor_idx]["data"]["id"]
        other_block_xor_id = self.graph["graph"][other_block_xor_idx]["data"]["id"]
        edges_out = self.id_edges["out"]
        this_join_xor_id = None
        other_join_xor_id = None
        # the blocks are identical, so it is possible to merge block nodes one by one
        for (this_edge_idx, this_edge), (other_edge_idx, other_edge) in zip(edges_out[this_block_xor_id].items(),
                                                                            edges_out[other_block_xor_id].items()):
            this_xor_succ_id = this_edge["data"]["target"]
            other_xor_succ_id = other_edge["data"]["target"]
            this_xor_succ_idx = self.get_label_by_id(this_xor_succ_id)
            other_xor_succ_idx = self.get_label_by_id(other_xor_succ_id)
            deep_merge_two_dicts(
                self.graph["graph"][this_xor_succ_idx]["data"]["variants"],
                self.graph["graph"][other_xor_succ_idx]["data"]["variants"])
            this_cur_succ_id = this_xor_succ_id
            other_cur_succ_id = other_xor_succ_id
            # blocks are identical, so it's enough to check for one of them
            while this_cur_succ_id in self.id_edges["out"]:
                this_cur_succ_id = edges_out[this_cur_succ_id][0]["data"]["target"]
                other_cur_succ_id = edges_out[other_cur_succ_id][0]["data"]["target"]
                this_cur_succ_idx = self.get_label_by_id(this_cur_succ_id)
                other_cur_succ_idx = self.get_label_by_id(other_cur_succ_id)

                # a nested block;
                # split xors will be merged in the recursive call
                if "_XOR_SPLIT" in this_cur_succ_id:
                    this_cur_succ_id, other_cur_succ_id = self.deep_merge_two_block(this_cur_succ_idx,
                                                                                    other_block_xor_idx)
                    continue  # join xors were already merged in the recursive call

                deep_merge_two_dicts(
                    self.graph["graph"][this_cur_succ_idx]["data"]["variants"],
                    self.graph["graph"][other_cur_succ_idx]["data"]["variants"])

                if "_XOR_JOIN" in this_cur_succ_id:
                    this_join_xor_id = this_cur_succ_id
                    other_join_xor_id = other_cur_succ_id
                    break

        return this_join_xor_id, other_join_xor_id


'''
    Merges dictionaries and nested dictionaries in these dictionaries.
    Helps to deep merge variants.
    Updates the first dictionary parameter directly, so makes no copy of it.
'''


def deep_merge_two_dicts(x, y):
    z = x
    for key in z:
        z[key].update(y[key])
    for key in y:
        if key not in z:
            z[key] = y[key].copy()
    return z
