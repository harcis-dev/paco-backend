class Event:
    #cases = {}  # {"case_1": "event_id_1", "case_4": "event_id_4", ...}

    def __init__(self, id, name):
        self.id = id
        self.name = name
        self.attributes = {}
