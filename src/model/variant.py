from src.configs import configs as ct
from src.model.case import Case


class Variant(Case):

    def __init__(self, c):
        super().__init__(c.id)
        self.cases = []
        self.events = c.events
