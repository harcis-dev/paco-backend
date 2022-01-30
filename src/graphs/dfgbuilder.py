from src.configs import configs as ct


def create_dfg(variants):
    pm = {"graph": []}

    # adding start and end nodes
    pm["graph"].append({"data": {"id": ct.DfgLabels.START, "label": ct.DfgLabels.START,
                                 "type": "node", "variants": {}}})
    pm["graph"].append({"data": {"id": ct.DfgLabels.END, "label": ct.DfgLabels.END,
                                 "type": "node", "variants": {}}})

    # edges will be added at the end of the graph creation,
    # so that they are placed separate from the nodes in the back part of the pm["graph"] array
    edges = []

    print("Starting with graph creation...")
    for idx, variant in enumerate(variants):  # FIXME DEBUG REMOVE IDX
        print(f"-- variant {variant.id}\t nr. {idx + 1}\t out of {len(variants)}")

        # all event ids (for each case) of the current event for the current variant,
        # e.g. for event A: {"case_0": "eventA_id_0", "case_1": "eventA_id_1"},
        # for empty: {"case_0": "", "case_1": ""}
        event_ids_empty = {}  # for start and end nodes and for edges

        # fill event_ids_empty with cases and empty event ids
        for case in variant.cases:
            event_ids_empty[case.id] = ""

        # start and end nodes are present in all the variants
        pm["graph"][0]["data"]["variants"][variant.id] = event_ids_empty
        pm["graph"][1]["data"]["variants"][variant.id] = event_ids_empty

        predecessor = ct.DfgLabels.START

        found_node = False  # if the event is already added to the graph
        found_edge = False  # if the edge is already present in the graph
        for event_idx, event in enumerate(variant.events):
            event_ids = {}  # for other nodes
            # set on false by every new iteration
            found_node = False
            found_edge = False

            # find all event ids (for each case) of the current event for the current variant
            for case in variant.cases:
                # the current event's index in the variant's list of events
                # corresponds to the current event's index in the case's list of events
                event_ids[case.id] = case.events[event_idx].id  # "case_0" : "event_id_0"

            for node in pm["graph"]:
                if node["data"]["label"] == event.name:
                    # add the current variant to the set of variants, in which the current element occurs
                    node["data"]["variants"][variant.id] = event_ids
                    found_node = True
                    break

            if found_node:  # searching for an edge only if the event was found/is already in the graph
                for edge in edges:
                    if edge["data"]["source"] == predecessor and edge["data"]["target"] == event.name:
                        # add the current variant to the map of variants of the edge
                        edge["data"]["variants"][variant.id] = event_ids_empty
                        found_edge = True
                        break
            else:  # the current element appears for the first time
                pm["graph"].append(
                    {"data": {"id": event.name, "label": event.name, "type": "node",
                              "variants": {variant.id: event_ids}}})

            if not found_edge:
                edges.append(
                    {"data": {"source": predecessor, "target": event.name, "label": "", "type": "DirectedEdge",
                              "variants": {variant.id: event_ids_empty}}})

            predecessor = event.name  # the current element (node) is the predecessor for the next one

        # adding an edge from the last event (node) of the variant to the end node
        found_edge = False
        if found_node:  # if the last node of the variant was found in the graph
            for edge in edges:
                if edge["data"]["source"] == predecessor and edge["data"]["target"] == ct.DfgLabels.END:
                    edge["data"]["variants"][variant.id] = event_ids_empty
                    found_edge = True
                    break

        if not found_edge:
            edges.append(
                {"data": {"source": predecessor, "target": ct.DfgLabels.END, "label": "",
                          "type": "DirectedEdge", "variants": {variant.id: event_ids_empty}}})

    pm["graph"] += edges

    print("graph created")

    return pm
