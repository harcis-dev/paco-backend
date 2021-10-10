from backend.eventlog.eventlog import EventLog


class SapEventLog(EventLog):
    def __init__(self, conn):
        self.conn = conn