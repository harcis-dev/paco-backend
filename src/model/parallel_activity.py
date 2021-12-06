class ParallelActivity:
    def __init__(self):
        self.outgoing_edges_count = -1
        self.incoming_edges_count = -1
        self.start_gateway_idx = -1
        self.end_gateway_idx = -1
        self.labels_path = []
        self.nodes_path = []
        self.event_count = {}

    def set_start_gateway(self, start_gateway_idx, outgoing_edges_count):
        self.start_gateway_idx = start_gateway_idx
        self.outgoing_edges_count = outgoing_edges_count

    def set_end_gateway(self, end_gateway_idx, incoming_edges_count):
        self.end_gateway_idx = end_gateway_idx
        self.incoming_edges_count = incoming_edges_count

    def add_event(self, event_idx, event_label):
        self.nodes_path.append(event_idx)
        self.labels_path.append(event_label)
        if event_label not in self.event_count:
            self.event_count[event_label] = 1
        else:
            self.event_count[event_label] = self.event_count[event_label] + 1
