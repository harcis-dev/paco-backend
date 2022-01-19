class ParallelActivity:
    def __init__(self):
        self.outgoing_edges_count = -1
        self.incoming_edges_count = -1
        self.start_gateway_idx = -1
        self.end_gateway_idx = -1
        self.id_path = []
        self.nodes_path = [set()]
        self.block_start_end = {}
        self.event_count = {}

    def set_start_gateway(self, start_gateway_idx, outgoing_edges_count):
        self.start_gateway_idx = start_gateway_idx
        self.outgoing_edges_count = outgoing_edges_count

    def set_end_gateway(self, end_gateway_idx, incoming_edges_count):
        self.end_gateway_idx = end_gateway_idx
        self.incoming_edges_count = incoming_edges_count

    def add_event(self, event_idx, event_label):
        self.nodes_path.append(event_idx)
        self.id_path.append(event_label)
        if event_label not in self.event_count:
            self.event_count[event_label] = 1
        else:
            self.event_count[event_label] = self.event_count[event_label] + 1

    def __repr__(self):
        return "ParallelActivity(%s, %s)" % (self.id_path, self.end_gateway_idx)

    def __eq__(self, other):
        if isinstance(other, ParallelActivity):
            return (self.id_path == other.id_path) and (self.end_gateway_idx == other.end_gateway_idx)
        else:
            return False

    def __hash__(self):
        return hash(self.__repr__())
