import io
import csv

from src.model.case import Case
from src.model.event import Event
from src.model.variant import Variant


def parse_csv(csv_file):
    if csv_file is None:
        return

    #stream = io.StringIO(csv_file.stream.read().decode("UTF8"), newline=None)
    with open('events.csv', newline=None) as stream:

        csvreader = csv.reader(stream)
        cases_dict = {}
        cases = []

        # 057_0,1,Kreditoren Rechnung,100,8001,2016,1900009869,2021-12-15 20:49:08.987209
        #len = sum(1 for line in stream)
        idx = 0
        for event_csv in csvreader:
            #print(f"Read {idx} out of {len}")

            cid = event_csv[0]
            if cid not in cases_dict:
                cases_dict[cid] = []

            e_name = event_csv[2]
            event = Event(f"{e_name}_{cid}_{idx}", e_name)
            event.attributes = {"bukrs": event_csv[4],
                                "pos": event_csv[1],
                                "gjahr": event_csv[5],
                                "mandt": event_csv[3],
                                "belnr": event_csv[6],
                                "timestamp": event_csv[7]}
            cases_dict[cid].append(event)
            idx += 1
            if idx == 1000: # TODO DEBUG
                break

        variants = []
        variants_footprints = []

        for cid, events in cases_dict.items():
            case = Case(cid)
            events.sort(key=lambda x: x.attributes["pos"])
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