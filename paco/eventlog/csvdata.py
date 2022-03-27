import io
import csv

from ..model.case import Case
from ..model.event import Event
from ..model.variant import Variant


def parse_csv(csv_file):
    stream = io.TextIOWrapper(csv_file.stream._file, "UTF8", newline=None)
    csv_dict = csv.DictReader(stream)

    cases_dict = {}
    cases = []

    # case id, position, activity, mandt, bukrs, gjahr, belnr, timestamp
    idx = 0
    for event_csv in csv_dict:
        cid = event_csv["case id"]
        if cid not in cases_dict:
            cases_dict[cid] = []

        e_name = event_csv["activity"]
        event = Event(f"{e_name.replace(' ', '_')}_{cid}_{idx}", e_name)

        attributes = event_csv
        del attributes["case id"], attributes["activity"]

        event.attributes = attributes
        cases_dict[cid].append(event)

        idx += 1
        if idx == 100: # TODO DEBUG
            break

    variants = []
    variants_footprints = []

    for cid, events in cases_dict.items():
        case = Case(cid)
        events.sort(key=lambda x: x.attributes["position"])
        case.events = events
        cases.append(cid)

        found_idx = -1
        for var_idx, var_footprint in enumerate(variants_footprints):
            if case == var_footprint:
                found_idx = var_idx

        if found_idx != -1:
            # check if the same case is already in variants
            for var_cid in variants[found_idx].cases:
                if cid == var_cid:
                    found_idx = -1
                if found_idx != -1:
                    variants[found_idx].cases.append(case)
                    break
        else:
            variants_footprints.append(case)
            variants.append(Variant(case))

    return variants