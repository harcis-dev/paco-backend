from backend.model.sequence import Sequence


class Variant(Sequence):
    sequences = []

    def __init__(self, s):
        Sequence.__init__(self, s.id)
        self.events = s.events # FIXME need deep copy?
        self.sequences.append(s.id)

        for e in self.events:
            e.attributes["Frequency"] = 1

    def add_sequence(self, s):
        for e in self.events:
            e.attributes["Frequency"] += 1

        self.sequences.append(s.id)