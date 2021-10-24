class ProcessModel:
    pm_dict = {}

    def __init__(self, variants):
        self.variants = variants

    def create(self):
        pm = {"frequency": {}, "graph": []}

        # adding start and end nodes
        pm["graph"].append({"data": {"id": "Start", "label": "Start", "type": "node", "variants": []}})
        pm["graph"].append({"data": {"id": "End", "label": "End", "type": "node", "variants": []}})

        # edges will be added at the end of the graph creation,
        # so that they are placed separate from the nodes in the back part of the pm["graph"] array
        edges = []

        print("Starting with graph creation...")
        for idx, variant in enumerate(self.variants): # FIXME DEBUG REMOVE IDX
            print(f"-- variant {variant.id}\t nr. {idx+1}\t out of {len(self.variants)}")
            # adding the variant and its number of cases to count event frequencies in the graph api back end
            pm["frequency"][variant.id] = len(variant.cases)
            # start and end nodes are present in all the variants
            pm["graph"][0]["data"]["variants"].append(variant.id)
            pm["graph"][1]["data"]["variants"].append(variant.id)
            predecessor = "Start"

            found_node = False  # if the event is already added to the graph
            found_edge = False  # if the edge is already present in the graph
            for event in variant.events:

                for node in pm["graph"]:
                    if node["data"]["id"] == event.name:
                        # add the current variant to the set of variants, in which the current element occurs
                        node["data"]["variants"].append(variant.id)
                        found_node = True
                        break

                if found_node:  # searching for an edge only if the event was found
                    for edge in edges:
                        if edge["data"]["source"] == predecessor and edge["data"]["source"] == event.name:
                            # add the current variant to the set of variants, in which the edge occurs
                            edge["data"]["variants"].append(variant.id)
                            found_edge = True
                            break
                else:  # the current element appears for the first time
                    pm["graph"].append(
                        {"data": {"id": event.name, "label": event.name, "type": "node", "variants": [variant.id]}})

                if not found_edge:
                    edges.append({"data": {"source": predecessor, "target": event.name, "label": "", "type": "DirectedEdge",
                                           "variants": [variant.id]}})

                predecessor = event.name  # the current element (node) is the predecessor for the next one

            # adding an edge from the last event (node) of the variant to the end node
            found_edge = False
            if found_node:  # if the last node of the variant was found in the graph
                for edge in edges:
                    if edge["data"]["source"] == predecessor and edge["data"]["source"] == "End":
                        # add the current variant to the set of variants, in which the edge occurs
                        edge["data"]["variants"].append(variant.id)
                        found_edge = True
                        break

            if not found_edge:
                edges.append(
                    {"data": {"source": predecessor, "target": "End", "label": "", "type": "DirectedEdge", "variants": [variant.id]}})

        pm["graph"] += edges

        print("graph created")

        self.pm_dict = pm
