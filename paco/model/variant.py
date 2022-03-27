from .case import Case


class Variant(Case):

    def __init__(self, c):
        super().__init__(c.id)
        self.cases = [c]
        self.events = c.events
