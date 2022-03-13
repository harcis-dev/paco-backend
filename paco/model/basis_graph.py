import math
from itertools import islice

from paco.model.event import Event
from paco.model.eventnode import EventNode
from paco.model.parallel_activity import ParallelActivity

from paco.configs import configs as ct

class BasisGraph:
    def __init__(self):
        self.graph = {"graph": []}
        # ids of successors of the start node
        self.start_nodes = []
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

        all_variants = {}
        artificial_start_node = {"data": {"id": "start", "label": "Start", "type": ct.BasisLabels.NODE,
                                          "variants": all_variants}}
        self.graph["graph"].append(artificial_start_node)
        self.events_by_index["start"] = 0
        print("Start node added")

        for idx, variant in enumerate(variants):  # FIXME DEBUG REMOVE IDX
            all_variants[variant.id] = {}
            var_event_pred = None
            found_node = None
            already_there = False
            for var_event_idx, var_event in enumerate(variant.events):
                event_ids = {}  # for event ids in cases
                found_node = None
                already_there = False

                # find all event ids (for each case) of the current event for the current variant
                for case in variant.cases:
                    event_id = case.events[var_event_idx].id
                    all_variants[variant.id][case.id] = event_id
                    # the current event's index in the variant's list of events
                    # corresponds to the current event's index in the case's list of events
                    event_ids[case.id] = event_id  # "case_0" : "event_id_0"
                    # DEBUG
                    # if var_event.id.split("_")[0] != case.events[var_event_idx].id.split("_")[0]:
                    #     print(f"{var_event.id.split('_')[0]} vs {case.events[var_event_idx].id.split('_')[0]}")
                    #     print(f"variant events: {variant.events}")
                    #     print(f"case events: {case.events}")
                    #     raise

                # find all identical events in variants;
                # are there any events with the same name as the var_event node (potentially in another variant)?
                if var_event.name in self.events_by_name:
                    # for all the events with this name
                    for event_by_name in self.events_by_name[var_event.name]:
                        # the event_by_name node and the var_event node has different predecessors,
                        # but maybe they have the same successors?
                        if not event_by_name.has_this_predecessor(var_event_pred):
                            # var_event is not the last node of its case
                            if var_event_idx != len(variant.events) - 1:
                                # successor of the var_event node
                                var_event_succ = variant.events[var_event_idx + 1]
                                # are there any events with the same successor as the var_event node?
                                if var_event_succ.name in self.events_by_name:
                                    # for all the events with the name as the successor of var_event
                                    for var_event_succ_by_name in self.events_by_name[var_event_succ.name]:
                                        # the successor of event_by_name has the same name as the var_event successor,
                                        # and the event_by_name is not the direct predecessor of var_event
                                        # (so that var_event_pred does not point to itself after merging)
                                        if event_by_name.has_this_successor(
                                                var_event_succ_by_name) and var_event_pred != event_by_name:
                                            # both event_by_name and var_event have at least one or no predecessor
                                            if (not event_by_name.predecessors) == var_event_pred is None:
                                                # var_event is already in the graph and corresponds to event_by_name
                                                found_node = event_by_name
                                                break

                                    if found_node is not None:
                                        already_there = True
                                        break
                            else:  # var_event is the last node of its case
                                # both event_by_name and var_event have at least one or no predecessor
                                # and the event_by_name node is also the last node of its case
                                # and the event_by_name is not the direct predecessor of var_event
                                # (so that var_event_pred does not point to itself after merging)
                                if (not event_by_name.predecessors) == var_event_pred is None and (
                                        not event_by_name.successors) and var_event_pred != event_by_name:
                                    found_node = event_by_name
                                    break

                                if found_node is not None:
                                    already_there = True
                                    break
                        else:  # the event_by_name node and the var_event node has the same predecessor
                            var_event_has_succ = var_event_idx != len(variant.events) - 1
                            # both event_by_name and var_event have at least one or no successor
                            # and the event_by_name is not the direct predecessor of var_event
                            # (so that var_event_pred does not point to itself after merging)
                            if bool(event_by_name.successors) == var_event_has_succ and var_event_pred != event_by_name:
                                found_node = event_by_name
                                already_there = True
                                break

                if found_node is None:
                    new_e = Event(f"{variant.id}_{var_event_idx}_{var_event.name}", var_event.name)

                    self.graph["graph"].append(
                        {"data": {"id": new_e.id, "label": new_e.name, "type": ct.BasisLabels.NODE,
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

                if var_event_pred is not None:
                    var_event_pred.successors.append(found_node)
                    found_node.predecessors.append(var_event_pred)

                    # searching for an edge only if the event was found/is already in the graph
                    found_edge = False
                    for edge in self.edges:
                        if edge["data"]["source"] == var_event_pred.event.id and \
                                edge["data"]["target"] == found_node.event.id:
                            # add the current variant to the map of variants of the edge
                            edge["data"]["variants"][variant.id] = event_ids
                            found_edge = True
                            break

                    if not found_edge:
                        new_edge = {
                            "data": {"id": f"{var_event_pred.event.id}_{found_node.event.id}",
                                     "source": var_event_pred.event.id, "target": found_node.event.id, "label": "",
                                     "type": "DirectedEdge", "variants": {variant.id: event_ids}}}
                        self.edges.append(new_edge)

                        # remember an index of the inserted edge in edges
                        edge_idx = len(self.edges) - 1

                        if found_node.event.id not in self.id_edges["in"]:
                            self.id_edges["in"][found_node.event.id] = {}
                        self.id_edges["in"][found_node.event.id][edge_idx] = new_edge

                        if var_event_pred.event.id not in self.id_edges["out"]:
                            self.id_edges["out"][var_event_pred.event.id] = {}
                        self.id_edges["out"][var_event_pred.event.id][edge_idx] = new_edge

                elif not already_there:
                    self.start_nodes.append(found_node.event.id)

                var_event_pred = found_node

            if not already_there:
                if found_node.event.name not in self.end_nodes:
                    self.end_nodes[found_node.event.name] = {}
                self.end_nodes[found_node.event.name][found_node.event.id] = found_node.node_idx

        if len(self.start_nodes) > 1:
            xor_node_id = f"start_XOR_SPLIT"

            # add the xor node to the graph
            self.graph["graph"].append(
                {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                          "variants": all_variants}})
            # remember an index of the inserted xor node
            node_idx = len(self.graph["graph"]) - 1
            self.events_by_index[xor_node_id] = node_idx
            print("Split xor added")

            # add an edge between the start node and the xor node
            new_edge_start_xor = {
                "data": {"id": f"start_{xor_node_id}", "source": "start", "target": xor_node_id, "label": "",
                         "type": "DirectedEdge", "variants": all_variants}}
            self.edges.append(new_edge_start_xor)

            edges_idx_start_xor = len(self.edges) - 1
            self.id_edges["out"]["start"] = {}
            self.id_edges["out"]["start"][edges_idx_start_xor] = new_edge_start_xor
            self.id_edges["in"][xor_node_id] = {}
            self.id_edges["in"][xor_node_id][edges_idx_start_xor] = new_edge_start_xor

            # edges from xor node to successors of the start node
            self.id_edges["out"][xor_node_id] = {}
            for startsucc_id in self.start_nodes:
                new_edge_xor_startsucc = {
                    "data": {"id": f"{xor_node_id}_{startsucc_id}", "source": xor_node_id, "target": startsucc_id,
                             "label": "",
                             "type": "DirectedEdge",
                             "variants": self.graph["graph"][self.events_by_index[startsucc_id]]["data"]["variants"]}}
                self.edges.append(new_edge_xor_startsucc)
                print(f"Start to {startsucc_id} edge added")

                edges_idx_xor_startsucc = len(self.edges) - 1
                self.id_edges["out"][xor_node_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
                self.id_edges["in"][startsucc_id] = {}
                self.id_edges["in"][startsucc_id][edges_idx_xor_startsucc] = new_edge_xor_startsucc
        else:
            # add an edge from the start node to its successor
            target_node = self.start_nodes[0]
            new_edge_start_startsucc = {
                "data": {"id": f"start_{target_node}", "source": "start", "target": target_node, "label": "",
                         "type": "DirectedEdge", "variants":
                             self.graph["graph"][self.events_by_index[target_node]]["data"][
                                 "variants"]}}
            self.edges.append(new_edge_start_startsucc)
            print(f"Start to {target_node} edge added")
            edges_idx_start_startsucc = len(self.edges) - 1
            self.id_edges["out"]["start"] = {}
            self.id_edges["out"]["start"][edges_idx_start_startsucc] = new_edge_start_startsucc
            self.id_edges["in"][target_node] = {}
            self.id_edges["in"][target_node][edges_idx_start_startsucc] = new_edge_start_startsucc

        print("Split XOR")
        # split xor operator
        for node_idx in range(len(self.graph["graph"])):
            node = self.graph["graph"][node_idx]
            node_type = node["data"]["type"]
            node_id = node["data"]["id"]
            node_variants = node["data"]["variants"]
            # the current node should have more than one out-edge for a split xor operator
            if node_type == "XOR" or node_id not in self.id_edges["out"] or len(self.id_edges["out"][node_id]) < 2:
                continue  # go to the next node

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
            new_edge_start_xor = {
                "data": {"id": f"{node_id}_{xor_node_id}", "source": node_id, "target": xor_node_id, "label": "",
                         "type": "DirectedEdge", "variants": node_variants}}
            self.edges.append(new_edge_start_xor)

            # remember an index of the inserted (current node -> xor)-edge in edges
            edge_idx_start_xor = len(self.edges) - 1

            # edges from xor node to successors of the current node
            self.id_edges["out"][xor_node_id] = {}
            for edge_idx, edge in self.id_edges["out"][node_id].items():
                target_node = edge["data"]["target"]
                new_edge_xor_startsucc = {
                    "data": {"id": f"{xor_node_id}_{target_node}", "source": xor_node_id, "target": target_node,
                             "label": "",
                             "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                self.edges.append(new_edge_xor_startsucc)

                # remember an index of the inserted (xor -> current node succ)-edge in edges
                edge_idx_xor_startsucc = len(self.edges) - 1

                self.id_edges["out"][xor_node_id][edge_idx_xor_startsucc] = new_edge_xor_startsucc
                self.id_edges["in"][target_node][edge_idx_xor_startsucc] = new_edge_xor_startsucc

                # remove the old edge from the graph;
                # the old ones will be replaced with None so as not to disrupt indexing
                # print(f'EDGE REMOVED: {self.edges[edge_idx]}')
                self.edges[edge_idx] = None

                # remove the old in-edges from the target node
                del self.id_edges["in"][target_node][edge_idx]
                if len(self.id_edges["in"][target_node]) == 0:
                    del self.id_edges["in"][target_node]

            # update in and out edge lists with the (current node -> xor)-edge
            self.id_edges["out"][node_id] = {}  # remove all the old edges
            self.id_edges["out"][node_id][edge_idx_start_xor] = new_edge_start_xor
            self.id_edges["in"][xor_node_id] = {}
            self.id_edges["in"][xor_node_id][edge_idx_start_xor] = new_edge_start_xor

        print("Join XOR")
        # join xor operator
        for node_idx in range(len(self.graph["graph"])):
            node = self.graph["graph"][node_idx]
            node_id = node["data"]["id"]
            node_type = node["data"]["type"]
            node_variants = node["data"]["variants"]
            # the current node should have more than one in-edge for a join xor operator
            if node_type == "XOR" or node_id not in self.id_edges["in"] or len(self.id_edges["in"][node_id]) < 2:
                continue  # go to the next node

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
            new_edge_xor_curnode = {
                "data": {"id": f"{xor_node_id}_{node_id}", "source": xor_node_id, "target": node_id, "label": "",
                         "type": "DirectedEdge", "variants": node_variants}}
            self.edges.append(new_edge_xor_curnode)

            # remember an index of the inserted (xor -> current node)-edge in self.edges
            edge_idx_xor_curnode = len(self.edges) - 1

            # self.edges from predecessors of the current node to the xor node
            self.id_edges["in"][xor_node_id] = {}
            for edge_idx, edge in self.id_edges["in"][node_id].items():
                source_node = edge["data"]["source"]
                new_edge_curnodepred_xor = {
                    "data": {"id": f"{source_node}_{xor_node_id}", "source": source_node, "target": xor_node_id,
                             "label": "",
                             "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                self.edges.append(new_edge_curnodepred_xor)

                # remember an index of the inserted (current node pred -> xor)-edge in self.edges
                edge_idx_curnodepred_xor = len(self.edges) - 1

                self.id_edges["in"][xor_node_id][edge_idx_curnodepred_xor] = new_edge_curnodepred_xor
                self.id_edges["out"][source_node][edge_idx_curnodepred_xor] = new_edge_curnodepred_xor

                # remove the old edge from the graph;
                # the old ones will be replaced with None so as not to disrupt indexing
                # print(f'EDGE REMOVED: {self.edges[edge_idx]}')
                self.edges[edge_idx] = None

                # remove the old out-edge from the source node
                del self.id_edges["out"][source_node][edge_idx]
                if len(self.id_edges["out"][source_node]) == 0:
                    del self.id_edges["out"][source_node]

            # update in and out edge lists with the (xor -> current node)-edge
            self.id_edges["in"][node_id] = {}  # remove all the old self.edges
            self.id_edges["in"][node_id][edge_idx_xor_curnode] = new_edge_xor_curnode
            self.id_edges["out"][xor_node_id] = {}
            self.id_edges["out"][xor_node_id][edge_idx_xor_curnode] = new_edge_xor_curnode

        print("End nodes join XOR")
        # join end nodes with a xor
        new_end_nodes = {}
        for end_node_name in self.end_nodes:
            if end_node_name not in new_end_nodes:
                new_end_nodes[end_node_name] = {}
            for node_id, node_idx in self.end_nodes[end_node_name].items():
                # if end node
                if node_id not in self.id_edges["out"]:
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
                        new_edge_xor_end = {"data": {"id": f"{xor_node_id}_{first_end_node_id}", "source": xor_node_id,
                                                     "target": first_end_node_id, "label": "",
                                                     "type": "DirectedEdge", "variants": end_node_variants}}
                        self.edges.append(new_edge_xor_end)

                        # remember an index of the inserted (xor -> end node)-edge in edges
                        edge_idx_xor_end = len(self.edges) - 1

                        # edges from predecessors of the end node to the xor node
                        self.id_edges["in"][xor_node_id] = {}
                        for edge_idx, edge in self.id_edges["in"][first_end_node_id].items():
                            source_node = edge["data"]["source"]
                            new_edge_endpred_xor = {
                                "data": {"id": f"{source_node}_{xor_node_id}", "source": source_node,
                                         "target": xor_node_id, "label": "",
                                         "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                            self.edges.append(new_edge_endpred_xor)

                            # remember an index of the inserted (end node pred -> xor)-edge in edges
                            edge_idx_endpred_xor = len(self.edges) - 1

                            self.id_edges["in"][xor_node_id][edge_idx_endpred_xor] = new_edge_endpred_xor
                            self.id_edges["out"][source_node][edge_idx_endpred_xor] = new_edge_endpred_xor

                            # remove the old edge from the graph;
                            # the old ones will be replaced with None so as not to disrupt indexing
                            # print(f'EDGE REMOVED: {self.edges[edge_idx]}')
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
                            "data": {"id": f"{source_node}_{xor_node_id}", "source": source_node, "target": xor_node_id,
                                     "label": "", "type": "DirectedEdge", "variants": edge["data"]["variants"]}}
                        self.edges.append(new_edge_endpred_xor)

                        # remember an index of the inserted (end node pred -> xor)-edge in edges
                        edge_idx_endpred_xor = len(self.edges) - 1

                        self.id_edges["in"][xor_node_id][edge_idx_endpred_xor] = new_edge_endpred_xor
                        self.id_edges["out"][source_node][edge_idx_endpred_xor] = new_edge_endpred_xor

                        # remove the old edge from the graph;
                        # the old ones will be replaced with None so as not to disrupt indexing
                        # print(f'EDGE REMOVED: {self.edges[edge_idx]}')
                        self.edges[edge_idx] = None

                        # remove the old out-edge from the source node
                        del self.id_edges["out"][source_node][edge_idx]

        print("Split AND")

        # join parallel activities (paths of events) with AND-connectors
        parallels_footprints = []
        parallels_pa = []

        for node_idx, node in enumerate(self.graph["graph"]):
            node_id = node["data"]["id"]
            # remember in parallels all paths from a xor-split-node to a xor-join-node
            if "_XOR_SPLIT" in node_id:  # if the node is a split xor operator
                # find all paths for every successor node of split xor to the nearest join xor (if exists)
                for edge_idx, edge in self.id_edges["out"][node_id].items():
                    xor_succ_type = self.graph["graph"][self.events_by_index[edge["data"]["target"]]]["data"]["type"]
                    # if the edge leads to another XOR-node, i.e. XOR -> XOR
                    if xor_succ_type == "XOR":  # SPLIT or JOIN
                        continue
                    else:
                        xor_succ_id = edge["data"]["target"]
                        pa = ParallelActivity()
                        pa.set_start_gateway(node_idx, len(self.id_edges["out"][node_id]))
                        self.find_parallels(xor_succ_id, pa)

                        # no join xor found
                        if pa.end_gateway_idx == -1: continue

                        # create an activity footprint as sorted array of events of an activity and gateway label
                        # so identical paths have the same footprint, regardless of the event order,
                        # if they flow into the same xor node.
                        # parallel activities should have the same join xor

                        footprint = pa.label_path

                        found_idx = -1
                        for pf_idx, par_footprint in enumerate(parallels_footprints):
                            # as the order doesn't matter (blocks will be correctly compared)
                            if ((len(footprint) == len(par_footprint)) and
                                    (all(i in par_footprint for i in footprint))):
                                found_idx = pf_idx

                        if found_idx != -1:
                            # check if an equal activity (with the same events order) is already in parallels
                            if pa not in parallels_pa[found_idx]:
                                parallels_pa[found_idx].append(pa)
                        else:
                            parallels_footprints.append(footprint)
                            parallels_pa.append([pa])

        # check if parallelism of activities present in parallels
        # for every footprint
        for fp_pas in parallels_pa:
            # number of events in the footprint activity
            size = len(fp_pas[0].label_path)
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
                for event_count in fp_pas[0].event_count:
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
                        for path_idx, node_idx in enumerate(pa.nodes_path):
                            # Same indices in nodes and labels paths reference same events
                            node_label = pa.label_path[path_idx]
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
                                    self.graph["graph"][unique_events[node_label]]["data"][
                                        "variants"] = deep_merge_two_dicts(
                                        self.graph["graph"][unique_events[node_label]]["data"]["variants"],
                                        self.graph["graph"][node_idx]["data"]["variants"])

                                # remove the old node from the graph;
                                # the old ones will be replaced with None so as not to disrupt indexing
                                self.graph["graph"][node_idx] = None
                                del self.events_by_index[node_id]

                            # remove in and out edges to the old node/block
                            if is_block:
                                self.remove_edges_block(node_id, pa.block_start_end[node_id])
                            else:
                                self.remove_edges_event(node_id)

                    # add the AND split node
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
                                "data": {"id": f"{and_node_id}_{node_id}", "source": and_node_id, "target": node_id,
                                         "label": "",
                                         "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_and_unique_event)
                            edge_idx_and_unique_event = len(self.edges) - 1
                            self.id_edges["in"][node_id] = {}
                            self.id_edges["in"][node_id][edge_idx_and_unique_event] = new_edge_and_unique_event
                            if and_node_id not in self.id_edges["out"]:
                                self.id_edges["out"][and_node_id] = {}
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
                                and_node_variants = deep_merge_two_dicts(and_node_variants, node_variants)
                            except StopIteration:
                                break

                        # add the AND node to the graph
                        self.graph["graph"].append(
                            {"data": {"id": and_node_id, "label": and_node_label, "type": and_node_type,
                                      "variants": and_node_variants}})
                        self.events_by_index[and_node_id] = len(self.graph["graph"]) - 1

                        # add an edge XOR -> AND
                        new_edge_xor_and = {
                            "data": {"id": f"{xor_node_id}_{and_node_id}", "source": xor_node_id, "target": and_node_id,
                                     "label": "", "type": "DirectedEdge", "variants": and_node_variants}}
                        self.edges.append(new_edge_xor_and)
                        edge_idx_xor_and = len(self.edges) - 1

                        self.id_edges["in"][and_node_id] = {}
                        self.id_edges["in"][and_node_id][edge_idx_xor_and] = new_edge_xor_and
                        self.id_edges["out"][xor_node_id][edge_idx_xor_and] = new_edge_xor_and

                        # add a new edge from the AND node to every unique event node
                        for unique_node_idx in unique_events.values():
                            node_id = self.graph["graph"][unique_node_idx]["data"]["id"]
                            node_variants = self.graph["graph"][unique_node_idx]["data"]["variants"]
                            new_edge_and_unique_event = {
                                "data": {"id": f"{and_node_id}_{node_id}", "source": and_node_id, "target": node_id,
                                         "label": "", "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_and_unique_event)
                            edge_idx_and_unique_event = len(self.edges) - 1
                            self.id_edges["in"][node_id] = {}
                            self.id_edges["in"][node_id][edge_idx_and_unique_event] = new_edge_and_unique_event
                            if and_node_id not in self.id_edges["out"]:
                                self.id_edges["out"][and_node_id] = {}
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
                                "data": {"id": f"{node_id}_{and_node_id}", "source": node_id, "target": and_node_id,
                                         "label": "", "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_unique_event_and)
                            edge_idx_unique_event_and = len(self.edges) - 1

                            if and_node_id not in self.id_edges["in"]:
                                self.id_edges["in"][and_node_id] = {}
                            self.id_edges["in"][and_node_id][edge_idx_unique_event_and] = new_edge_unique_event_and
                            self.id_edges["out"][node_id] = {}
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
                                    node_variants = self.graph["graph"][unique_events[next(ue_iter)]]["data"][
                                        "variants"]
                                    and_node_variants = deep_merge_two_dicts(and_node_variants, node_variants)
                                except StopIteration:
                                    break

                        # add the AND node to the graph
                        self.graph["graph"].append(
                            {"data": {"id": and_node_id, "label": and_node_label, "type": and_node_type,
                                      "variants": and_node_variants}})
                        self.events_by_index[and_node_id] = len(self.graph["graph"]) - 1

                        # add an edge AND -> XOR
                        new_edge_and_xor = {
                            "data": {"id": f"{and_node_id}_{xor_node_id}", "source": and_node_id, "target": xor_node_id,
                                     "label": "", "type": "DirectedEdge", "variants": and_node_variants}}
                        self.edges.append(new_edge_and_xor)
                        edge_idx_and_xor = len(self.edges) - 1

                        self.id_edges["in"][xor_node_id][edge_idx_and_xor] = new_edge_and_xor
                        self.id_edges["out"][and_node_id] = {}
                        self.id_edges["out"][and_node_id][edge_idx_and_xor] = new_edge_and_xor

                        # add a new edge from every unique event node to the AND node
                        for unique_node_idx in unique_events.values():
                            node_id = self.graph["graph"][unique_node_idx]["data"]["id"]
                            node_variants = self.graph["graph"][unique_node_idx]["data"]["variants"]
                            new_edge_unique_event_and = {
                                "data": {"id": f"{node_id}_{and_node_id}", "source": node_id, "target": and_node_id,
                                         "label": "", "type": "DirectedEdge", "variants": node_variants}}
                            self.edges.append(new_edge_unique_event_and)
                            edge_idx_unique_event_and = len(self.edges) - 1

                            if and_node_id not in self.id_edges["in"]:
                                self.id_edges["in"][and_node_id] = {}
                            self.id_edges["in"][and_node_id][edge_idx_unique_event_and] = new_edge_unique_event_and
                            self.id_edges["out"][node_id] = {}
                            self.id_edges["out"][node_id][edge_idx_unique_event_and] = new_edge_unique_event_and

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
            event_label = self.graph["graph"][node_idx]["data"]["label"]

            if "_XOR_JOIN" in node_id:
                pa.set_end_gateway(node_idx, len(edges_in[node_id]))
                break

            if "_XOR_SPLIT" in node_id:
                # node_id is now a join xor of the block or a graph leaf
                end_node_id, event_label = self.add_block_iter(node_id)
                # node_id is the split xor
                pa.block_start_end[node_id] = end_node_id
                # node_id is now the join xor
                node_id = end_node_id

            # add an event label or a block footprint to the parallel activity
            pa.add_event(node_idx, event_label)

            # if the node is not a leaf
            if node_id in edges_out:
                stack.append(next(iter(edges_out[node_id].values()))["data"]["target"])

    '''
    RECURSIVE VERSION
        pa blocks: [{E: [E, D], J: [J, {H: [H,...], F: {F, G}}]}]
    '''

    def add_block_rec(self, split_xor_id):
        block = {}
        edges_out = self.id_edges["out"]
        join_xor_id = None
        cur_succ_id = None

        for edge_idx, edge in edges_out[split_xor_id].items():
            xor_succ_id = edge["data"]["target"]  # xor successor (cannot be another xor)
            xor_succ_label = self.get_label_by_id(xor_succ_id)
            # remember the first node of every xor branch to sort the block
            block[xor_succ_label] = [xor_succ_label]
            cur_succ_id = xor_succ_id
            while cur_succ_id in self.id_edges["out"]:
                # there is only one successor possible
                cur_succ_id = next(iter(edges_out[cur_succ_id].values()))["data"]["target"]

                if "_XOR_JOIN" in cur_succ_id:
                    join_xor_id = cur_succ_id
                    block[xor_succ_label].append(self.get_label_by_id(join_xor_id))
                    break

                # a nested block
                if "_XOR_SPLIT" in cur_succ_id:
                    cur_succ_id, nested_block = self.add_block_rec(cur_succ_id)
                    # store a block footprint as its label
                    block[xor_succ_label].append(nested_block)
                else:
                    block[xor_succ_label].append(self.get_label_by_id(cur_succ_id))

        # block footprint will be saved as a node label of pa (one block = one pa node)
        str_block = str(dict(sorted(block.items())))
        if join_xor_id is not None:
            cur_succ_id = join_xor_id
        return cur_succ_id, str_block  # join xor or a graph leaf

    '''
    ITERATIVE VERSION (with stack)
        pa blocks: [{E: [E, D], J: [J, {H: [H,...], F: {F, G}}]}]
    '''

    def add_block_iter(self, split_xor_id):
        # create a stack for the frist node of nested blocks
        stack = []

        block = {}
        # push a tuple of the split_xor and a reference to "block"
        stack.append((split_xor_id, block))

        edges_out = self.id_edges["out"]
        end_node_id = None

        while len(stack):
            # next nested block (opening xor node)
            block_xor_id, curr_block = stack.pop()

            join_xor_id = None

            for edge_idx, edge in edges_out[block_xor_id].items():
                xor_succ_id = edge["data"]["target"]  # xor successor (cannot be another xor)
                xor_succ_label = self.get_label_by_id(xor_succ_id)
                # remember the first node of every xor branch to sort the block
                curr_block[xor_succ_label] = [xor_succ_label]
                cur_succ_id = xor_succ_id
                while cur_succ_id in self.id_edges["out"]:  # condition for graph leaves; on join xor will be breaked
                    # there is only one successor possible (for not split xor nodes)
                    cur_succ_id = next(iter(edges_out[cur_succ_id].values()))["data"]["target"]

                    if "_XOR_JOIN" in cur_succ_id:
                        join_xor_id = cur_succ_id
                        curr_block[xor_succ_label].append(self.get_label_by_id(join_xor_id))
                        break

                    # a nested block
                    if "_XOR_SPLIT" in cur_succ_id:
                        curr_block[xor_succ_label].append({})
                        # block will be filled via reference
                        # code example https://replit.com/@IliaBudnikov/addingblockviaref#main.py
                        stack.append((cur_succ_id, curr_block[xor_succ_label][-1]))
                        # skipping the block, as it will be traced in the next stack iteration
                        cur_succ_id = self.find_block_end(cur_succ_id)
                    else:
                        curr_block[xor_succ_label].append(self.get_label_by_id(cur_succ_id))

                # only set the first join xor found;
                # otherwise, the end node can be set from one of the nested blocks.
                if end_node_id is None:
                    if join_xor_id is not None:
                        end_node_id = join_xor_id
                    else:
                        end_node_id = cur_succ_id

        return end_node_id, block  # join xor or a graph leaf

    '''
        Finds the end of the block (join xor id or in case of non-existence one of the leaves)
    '''

    def find_block_end(self, node_id):
        # create a stack for dfs
        stack = []

        # a node cannot be revisited in this type of graph:
        # if two or more paths lead to the same node,
        # then this node is an operator (in this case xor).

        # push the current source node
        stack.append(node_id)
        edges_out = self.id_edges["out"]

        # a nested block detected -> +1,
        # the end (leaf of join xor) of a block reached and the value > 0? -> -1
        # a join xor found and the value is 0? -> break, else continue searching
        # no more successors and no join xors were found? -> return None
        block_counter = 0

        while len(stack):
            # next node
            node_id = stack.pop()

            if "_XOR_JOIN" in node_id:
                if block_counter == 0:
                    return node_id
                else:
                    block_counter -= 1

            if "_XOR_SPLIT" in node_id:
                block_counter += 1

            if node_id in edges_out:
                for edge_idx, edge in edges_out[node_id].items():
                    stack.append(edge["data"]["target"])

        return node_id

    '''
        Removes all edges (in and out) from the edges dict for a node id
    '''

    def remove_edges_event(self, event_id):
        self.remove_edges(event_id, "in")
        self.remove_edges(event_id, "out")

    def remove_edges_block(self, block_start_id, block_end_id):
        self.remove_edges(block_start_id, "in")
        self.remove_edges(block_end_id, "out")

    def get_label_by_id(self, node_id):
        node_idx = self.events_by_index[node_id]
        return self.graph["graph"][node_idx]["data"]["label"]

    def deep_merge_two_block(self, this_block_xor_idx, other_block_xor_idx):
        # merge split xor operators of the two block
        self.graph["graph"][this_block_xor_idx]["data"]["variants"] = deep_merge_two_dicts(
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
            self.graph["graph"][this_xor_succ_idx]["data"]["variants"] = deep_merge_two_dicts(
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

                self.graph["graph"][this_cur_succ_idx]["data"]["variants"] = deep_merge_two_dicts(
                    self.graph["graph"][this_cur_succ_idx]["data"]["variants"],
                    self.graph["graph"][other_cur_succ_idx]["data"]["variants"])

                if "_XOR_JOIN" in this_cur_succ_id:
                    this_join_xor_id = this_cur_succ_id
                    other_join_xor_id = other_cur_succ_id
                    break

        return this_join_xor_id, other_join_xor_id

    def remove_node(self, node_idx):
        node_id = self.graph["graph"][node_idx]["data"]["id"]
        self.graph["graph"][node_idx] = None
        del self.events_by_index[node_id]
        self.remove_edges(node_id, "in")
        self.remove_edges(node_id, "out")

    def remove_edges(self, node_id, direction):
        if node_id in self.id_edges[direction]:
            edges_to_remove = self.id_edges[direction][node_id]
            for edge_idx_to_remove in edges_to_remove:
                if direction == "in":  # delete the corresponding out-edge of predecessor
                    pred_id = self.edges[edge_idx_to_remove]["data"]["source"]
                    if pred_id in self.id_edges["out"]:
                        del self.id_edges["out"][pred_id][edge_idx_to_remove]
                        if len(self.id_edges["out"][pred_id]) == 0:
                            del self.id_edges["out"][pred_id]
                else:  # delete the corresponding in-edge of successor
                    succ_id = self.edges[edge_idx_to_remove]["data"]["target"]
                    if succ_id in self.id_edges["in"]:
                        del self.id_edges["in"][succ_id][edge_idx_to_remove]
                        if len(self.id_edges["in"][succ_id]) == 0:
                            del self.id_edges["in"][succ_id]
                self.edges[edge_idx_to_remove] = None
            del self.id_edges[direction][node_id]

    def merge_paths(self, graph_type=None):
        changed = True
        while changed:
            changed = False
            for node_idx in range(len(self.graph["graph"])):
                if self.graph["graph"][node_idx] is None:
                    continue  # one of deleted xor successors

                node_id = self.graph["graph"][node_idx]["data"]["id"]
                node_type = self.graph["graph"][node_idx]["data"]["type"]
                if "_XOR_SPLIT" in node_id and node_type == "XOR":
                    # successor label -> [original successor index, new xor index, original succ -> new xor edge index]
                    unique_events = {}
                    # check all the xor successors
                    for edges_idx_succ, edge_succ in self.id_edges["out"][node_id].copy().items():
                        succ_id = edge_succ["data"]["target"]
                        succ_idx = self.events_by_index[succ_id]

                        succ_type = self.graph["graph"][succ_idx]["data"]["type"]
                        if succ_type not in ct.NODE_TYPES:
                            continue

                        succ_label = self.graph["graph"][succ_idx]["data"]["label"]

                        if succ_label not in unique_events:  # operators schouldn't be merged
                            unique_events[succ_label] = [succ_idx, None, None]  # original xor successor
                        else:
                            changed = True  # the graph will be changed here
                            # add successor xor node
                            # if a xor successor, that is identical to the original xor successor, has its own successors
                            if succ_id in self.id_edges["out"]:
                                if unique_events[succ_label][1] is None:  # if no xor added yet
                                    # adding the new xor node
                                    xor_node_id = f'{self.graph["graph"][unique_events[succ_label][0]]["data"]["id"]}_XOR_SPLIT'
                                    self.graph["graph"].append(
                                        {"data": {"id": xor_node_id, "label": "X", "type": "XOR",
                                                  "variants": None}})  # variants will be added later
                                    unique_events[succ_label][1] = len(self.graph["graph"]) - 1
                                    self.events_by_index[xor_node_id] = unique_events[succ_label][1]

                                    # original xor successor
                                    orig_node_id = self.graph["graph"][unique_events[succ_label][0]]["data"]["id"]

                                    # if the original xor successor has successors
                                    if orig_node_id in self.id_edges["out"]:
                                        # add an edge between the new xor node and the successor of the original xor successor
                                        for edges_idx_succ, edge_succ in self.id_edges["out"][orig_node_id].items():
                                            succ_node = edge_succ["data"][
                                                "target"]  # successor of the original xor successor
                                            new_edge_xor_origsuccnode = {
                                                "data": {"id": f"{xor_node_id}_{succ_node}", "source": xor_node_id,
                                                         "target": succ_node, "label": "",
                                                         "type": "DirectedEdge",
                                                         "variants": edge_succ["data"]["variants"]}}
                                            self.edges.append(new_edge_xor_origsuccnode)

                                            # remember an index of the inserted (new xor -> succ of the original xor succ)-edge in edges
                                            edges_idx_xor_curnodesucc = len(self.edges) - 1

                                            self.id_edges["in"][succ_node] = {}
                                            self.id_edges["in"][succ_node][
                                                edges_idx_xor_curnodesucc] = new_edge_xor_origsuccnode
                                            self.id_edges["out"][xor_node_id] = {}
                                            self.id_edges["out"][xor_node_id][
                                                edges_idx_xor_curnodesucc] = new_edge_xor_origsuccnode

                                            # remove the old edge from the graph;
                                            # the old ones will be replaced with None so as not to disrupt indexing
                                            self.edges[edges_idx_succ] = None

                                    # add an edge between the original xor successor and the new xor node
                                    new_edge_cur_xor = {
                                        "data": {"id": f"{orig_node_id}_{xor_node_id}", "source": orig_node_id,
                                                 "target": xor_node_id, "label": "",
                                                 "type": "DirectedEdge",
                                                 "variants": None}}  # variants will be added later
                                    self.edges.append(new_edge_cur_xor)

                                    # remember an index of the inserted (original xor succ -> new xor)-edge in edges
                                    edge_idx_cur_xor = len(self.edges) - 1
                                    # assign the new xor node to the original xor successor
                                    unique_events[succ_label][2] = edge_idx_cur_xor

                                    # remove the out-edge of the original xor successor
                                    self.id_edges["out"][orig_node_id] = {}
                                    # add the edge to the new xor node
                                    self.id_edges["out"][orig_node_id][edge_idx_cur_xor] = new_edge_cur_xor
                                    self.id_edges["in"][xor_node_id] = {}
                                    self.id_edges["in"][xor_node_id][edge_idx_cur_xor] = new_edge_cur_xor

                                # add an edge between the new xor and the successor of the identical xor successor
                                for edge_idx_idec, edge_idec in self.id_edges["out"][succ_id].items():
                                    succ_idec = edge_idec["data"]["target"]
                                    xor_node_id = self.graph["graph"][unique_events[succ_label][1]]["data"]["id"]
                                    new_edge_xor_succidec = {
                                        "data": {"id": f"{xor_node_id}_{succ_idec}", "source": xor_node_id,
                                                 "target": succ_idec, "label": "", "type": "DirectedEdge",
                                                 "variants": edge_idec["data"]["variants"]}}
                                    self.edges.append(new_edge_xor_succidec)

                                    # remember an index of the inserted (new xor -> succ of the identical xor succ)-edge in edges
                                    edge_idx_xor_succidec = len(self.edges) - 1

                                    if xor_node_id not in self.id_edges[
                                        "out"]:  # if the original node has no successors
                                        self.id_edges["out"][xor_node_id] = {}
                                    self.id_edges["out"][xor_node_id][edge_idx_xor_succidec] = new_edge_xor_succidec
                                    # edge from succ_idec to its predecessor will be removed later in remove_node()
                                    self.id_edges["in"][succ_idec][edge_idx_xor_succidec] = new_edge_xor_succidec

                            # add all variants of the identical xor successor to the original xor successor
                            self.graph["graph"][unique_events[succ_label][0]]["data"][
                                "variants"] = deep_merge_two_dicts(
                                self.graph["graph"][unique_events[succ_label][0]]["data"]["variants"],
                                self.graph["graph"][succ_idx]["data"]["variants"])

                            # remove the identical xor successor
                            self.remove_node(succ_idx)

                    # set variants of the new xors and edges between the original xor successors and the new xors
                    for succ_xor in unique_events.values():
                        # if a new xor was added
                        if succ_xor[1] is not None:
                            # variants of the current original xor successor
                            succ_variants = self.graph["graph"][succ_xor[0]]["data"]["variants"]
                            # in-edge of the original xor successor
                            in_edge = \
                            list(self.id_edges["in"][self.graph["graph"][succ_xor[0]]["data"]["id"]].values())[0]
                            # set variants of the original xor successor to its in-edge
                            in_edge["data"]["variants"] = succ_variants
                            # set variants of the original xor successor to the new xor
                            self.graph["graph"][succ_xor[1]]["data"]["variants"] = succ_variants
                            # set variants of the original xor successor to the edge
                            # between the original xor successor and the new xor
                            self.edges[succ_xor[2]]["data"]["variants"] = succ_variants

                    # if all the successors of the split xor were identical,
                    # remove the xor operator, as they were merged to one node
                    if len(self.id_edges["out"][node_id]) == 1:
                        pred_id = next(iter(self.id_edges["in"][node_id].values()))["data"]["source"]

                        # remove the split operator
                        self.remove_node(self.events_by_index[node_id])

                        if graph_type == "epc":
                            # remove function node before the split xor, that was removed
                            if "_XOR_SPLIT" in pred_id:
                                # predecessor node of the function which precedes the split xor
                                # should be connected with the successor of the split xor
                                function_id = pred_id
                                pred_id = next(iter(self.id_edges["in"][function_id].values()))["data"]["source"]

                                # remove the function node
                                self.remove_node(self.events_by_index[function_id])

                        # successor of the split xor
                        succ_idx = list(unique_events.values())[0][0]  # only one original xor successor
                        succ_id = self.graph["graph"][succ_idx]["data"]["id"]

                        # add an edge between the predecessor and the successor of the split xor
                        new_edge_pred_succ = {
                            "data": {"id": f"{pred_id}_{succ_id}", "source": pred_id,
                                     "target": succ_id,
                                     "label": "",
                                     "type": "DirectedEdge",
                                     "variants": self.graph["graph"][succ_idx]["data"]["variants"]}}
                        self.edges.append(new_edge_pred_succ)

                        # remember an index of the inserted (pred -> succ)-edge in edges
                        edge_idx_pred_succ = len(self.edges) - 1

                        self.id_edges["out"][pred_id] = {}
                        self.id_edges["out"][pred_id][edge_idx_pred_succ] = new_edge_pred_succ
                        self.id_edges["in"][succ_id] = {}
                        self.id_edges["in"][succ_id][edge_idx_pred_succ] = new_edge_pred_succ

            if not changed: break


'''
    Merges dictionaries and nested dictionaries in these dictionaries.
    Helps to deep merge variants.
    Updates the first dictionary parameter directly, so makes no copy of it.
'''


def deep_merge_two_dicts(x, y):
    z = x.copy()
    for key in z:
        if key in y:
            z[key].update(y[key])
    for key in y:
        if key not in z:
            z[key] = y[key].copy()
    return z