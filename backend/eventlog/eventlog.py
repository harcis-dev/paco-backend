class EventLog:
    sequences = []

    def variants(self):
        variants_by_footprint = {}
        for s in self.sequences:
            variants_by_footprint.setdefault(s.footprint(), []).append(s)

        return variants_by_footprint.values()