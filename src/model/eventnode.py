'''
    This is an normal event, but with some additional functionality to be handled like a graph node
'''


class EventNode:
    def __init__(self, event, nodes_idx):
        self.event = event
        self.nodes_idx = nodes_idx
        self.predecessors = []
        self.successors = []

    def has_this_predecessor(self, other_event_pred):
        # Start nodes, no predecessors
        if other_event_pred is None and not self.predecessors:
            return True

        if other_event_pred is not None:
            for predecessor in self.predecessors:
                if other_event_pred.event.name == predecessor.event.name:
                    # Other event has the same predecessor
                    return True

        return False

    def has_this_successor(self, other_event_succ):
        # End nodes, no predecessors
        if other_event_succ is None and not self.successors:
            return True

        if other_event_succ is not None:
            for successor in self.successors:
                if other_event_succ.event.name == successor.event.name:
                    # Other event has the same successor
                    return True

        return False

    '''
    def has_this_successor_id(self, other_event_succ):
        if other_event_succ is not None:
            for successor in self.successors:
                if other_event_succ.event.id == successor.event.id:
                    return True

        return False
    '''

    def __eq__(self, other):
        if not isinstance(other, EventNode):
            return False

        return self.event.name == other.event.name
