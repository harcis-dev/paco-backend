class Case:

    def __init__(self, id):
        self.id = id
        self.events = []

    def footprint(self):
        footprint = "["

        for e in self.events:
            footprint += e.name + ", "

        footprint = footprint[:-2] + "]"  # remove the last ", "

        return footprint

    def __eq__(self, other):
        if not isinstance(other, Case):
            return False

        return self.id == other.id or self.footprint() == other.footprint()
