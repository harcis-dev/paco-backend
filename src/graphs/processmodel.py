import networkx as nx
from src.configs import constants as ct


class ProcessModel:
    G = None

    def __init__(self, variants):
        self.variants = variants

    def create(self):
        G = nx.DiGraph()
        G.add_node("Start", Frequency=0)
        G.add_node("End", Frequency=0)

        for variant in self.variants:
            predecessor = None

            for event in variant.events:
                freq_attr = event.attributes(ct.Attributes.FREQUENCY)

                '''
                Note:
                G.nodes['node'] -> a dict with attributes of the note 'node, e.g. {'Frequency': 3}
                G['node'] -> a dict with successors with their attributes, e.g. {'succ': {'Frequency': 4}}
                '''

                # Is the event already present in the graph as a node?
                try:
                    current_node = G.nodes[event.id]  # throws KeyError, if node with event id not found

                    # event (node) with that id was found in the graph
                    current_node[ct.Attributes.FREQUENCY] += freq_attr
                except KeyError:
                    # no event (node) with that id in the graph
                    G.add_node(event.id, Frequency=freq_attr)

                # Is the current event the first event in the case?
                if predecessor is None:
                    predecessor = "Start"  # start node is now the predecessor of the current node
                    G.nodes[predecessor][ct.Attributes.FREQUENCY] += freq_attr

                # Is the edge from the predecessor to the current node already present in the graph?
                try:
                    edge_pred_currnode = G[predecessor][event.id]

                    # the edge was found in the graph
                    edge_pred_currnode[ct.Attributes.FREQUENCY] += freq_attr
                except KeyError:
                    # no edge from the predecessor to the current node was found in the graph
                    G.add_edge(predecessor, event.id, Frequency=freq_attr)

                predecessor = event.id

            # Is the edge from the last event (node) to the end node already present in the graph?
            try:
                edge_lastnode_endnode = G[predecessor]["End"]

                # the edge was found in the graph -> edge frequency += last node frequency
                edge_lastnode_endnode[ct.Attributes.FREQUENCY] += G.nodes[predecessor][ct.Attributes.FREQUENCY]
            except KeyError:
                # no edge was found
                G.add_edge(predecessor, "End", Frequency=G.nodes[predecessor][ct.Attributes.FREQUENCY])

        self.G = G
