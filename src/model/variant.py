from src.configs import configs as ct
from src.model.case import Case


class Variant(Case):
    #cases_with_events = {}  # {"case_0": ["event_1", "event_2", "event_3"], "case_1": ["event_1", "event_3"], ...}

    def __init__(self, c):
        super().__init__(c.id)
        self.cases = []
        self.events = c.events
