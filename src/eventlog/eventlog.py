from src.model.variant import Variant


class EventLog:
    sequences = []

    def variants(self):
        variants_by_footprint = {}
        for s in self.sequences:
            variants_by_footprint.setdefault(s.footprint(), Variant(s)).add_sequence(s)

        return variants_by_footprint.values()