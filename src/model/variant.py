from src.configs import constants as ct
from src.model.case import Case


class Variant(Case):
    cases = []

    def __init__(self, c):
        super().__init__(c.id)
        self.events = c.events # FIXME need deep copy?
        self.cases.append(c.id)

        for e in self.events:
            e.attributes[ct.Attributes.FREQUENCY] = 1

    def add_case(self, c):
        for e in self.events:
            e.attributes[ct.Attributes.FREQUENCY] += 1

        self.cases.append(c.id)