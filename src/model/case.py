class Case:

    def __init__(self, id):
        self.id = id
        self.events = []

    def __eq__(self, other):
        if not isinstance(other, Case):
            return False

        return self.id == other.id or self.events == other.events
