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
                            if idx != len(variant.events)-1:
                                # successor of the current var_event
                                var_event_succ = variant.events[idx+1]
                                if var_event_succ.name in events_by_name:
                                    for event_succ_by_name in events_by_name[var_event_succ.name]:
                                        if event_by_name.has_this_successor(event_succ_by_name) and var_event_pred != event_by_name:
                                            if var_event_pred != event_by_name and bool(event_by_name.predecessors) == var_event_pred is not None:
                                                found_node = event_by_name
                                                break

                                    if found_node is not None:
                                        event_node = found_node
                                        already_there = True
                                        break
                            else:
                                if var_event_pred is None == (not event_by_name.predecessors) and (not event_by_name.successors) and var_event_pred != event_by_name:
                                    found_node = event_by_name
                                    break

                                if found_node is not None:
                                        event_node = found_node
                                    already_there = True
                                    break
                        else:
                            var_event_has_succ = idx != len(variant.events)-1
                            if bool(event_by_name.successors) == var_event_has_succ and var_event_pred != event_by_name:
                                found_node = event_by_name
                                already_there = True
                                break

                if found_node is None:
                    e_new = Event(f"{variant.id}_{idx}_{var_event.name}", var_event.name)

                    epc["graph"].append(
                        {"data": {"id": e_new.id, "label": e_new.name, "type": "Event",
                                  "variants": {variant.id: event_ids}}})

                    if e_new.name not in events_by_name:
                        events_by_name[e_new.name] = []

                    found_node = EventNode(e_new)
                    events_by_name[e_new.name].append(found_node)
                    print(f"new foundEvent: {found_node.event.id}")
                else:
                    epc["graph"][0]["data"]["variants"][variant.id] = event_ids
                    print(f"foundEvent: {found_node.event.id}")

                event_node = found_node
                if var_event_pred is not None:
                    var_event_pred.successors.append(event_node)
                    event_node.predecessors.append(var_event_pred)

                    # searching for an edge only if the event was found/is already in the graph
                    found_edge = False
                    for edge in edges:
                        if edge["data"]["source"] == var_event_pred.event.id and edge["data"]["target"] == event_node.event.id:
                            # add the current variant to the map of variants of the edge
                            edge["data"]["variants"][variant.id] = event_ids
                            found_edge = True
                            break

                    if not found_edge:
                        edge_new = {"data": {"source": var_event_pred.event.id, "target": event_node.event.id, "label": "",
                                      "type": "DirectedEdge", "variants": {variant.id: event_ids}}}
                        edges.append(edge_new)

                        if event_node.event.id not in id_edges["in"]:
                            id_edges["in"][event_node.event.id] = []
                        id_edges["in"][event_node.event.id].append(edge_new)

                        if var_event_pred.event.id not in id_edges["out"]:
                            id_edges["out"][var_event_pred.event.id] = []
                        id_edges["out"][var_event_pred.event.id].append(edge_new)

                elif not already_there:
                    if var_event.name not in start_nodes:
                        start_nodes[var_event.name] = [event_node.event.id]
                    elif start_nodes[var_event.name]:
                        start_nodes[var_event.name].append(event_node.event.id)

                var_event_pred = event_node

            if not already_there:
                if event_node.event.name not in end_nodes:
                    end_nodes[event_node.event.name] = [event_node.event.id]
                elif end_nodes[event_node.event.name]:
                    end_nodes[event_node.event.name].append(event_node.event.id)

            for node in epc["graph"]:
                node_name = node["data"]["label"]
                node_id = node["data"]["id"]
                if node_name in start_nodes and node_id in start_nodes[node_name]:
                    edges_in = 0
                    for edge in id_edges["in"][node_id]:
                        edges_in += 1
                        break
                    if edges_in == 0:
                        continue

                edges_out = len(id_edges["out"][node_id])
                if edges_out > 1:
                    # the current node has at least one in edge and more than one out edge;
                    # insert a xor operator between the current node and it's successors
                    epc["graph"].append(
                        {"data": {"id": f"{node_id}_XOR_SPLIT", "label": "X", "type": "XOR",
                                  "variants": {variant.id: event_ids}}})



        epc["graph"] += edges

        print("graph created")

        self.epc_dict = epc
