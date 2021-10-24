from src.model.variant import Variant


class EventLog:
    cases = []

    def variants(self):
        variants_by_footprint = {}
        for c in self.cases:
            variants_by_footprint.setdefault(c.footprint(), Variant(c)).add_case(c)

        return variants_by_footprint.values()