class Case:

    def __init__(self, id):
        self.id = id
        self.events = []

    def __eq__(self, other):
        if not isinstance(other, Case):
            return False

        if self.id == other.id:
            return True

        if len(self.events) != len(other.events):
            return False

        for event_idx in range(len(self.events)):
            if self.events[event_idx].name != other.events[event_idx].name:
                return False

        return True
