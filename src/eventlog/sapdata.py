import json
from itertools import islice

import src.app
from src.databases.mariadb_services import mariadb_service
from src.model.case import Case
from src.model.event import Event
from src.model.variant import Variant

# FIXME DEBUG
from src.configs import configs as ct

class Filter:
    DEBITORS = "KUNNR"
    CREDITORS = "LIFNR"
    ACCOUNTS = "HKONT"
    USERS = "USNAM"
    FIXED_ASSETS = "ANLN1"

'''
    Reads data from MariaDB and initializes cases
'''

def read_sap_data(filters):
    case_ids = set()

    '''
    print("Reading data...")
    # array of filters is None or empty
    if filters is None or not filters:
        case_ids = mariadb_service.all_cases()
    else:
        for filter in filters.keys():
            filter_case_ids = mariadb_service.filter_cases(filter, filters[filter])
            if filter_case_ids and case_ids:
                case_ids = case_ids.intersection(filter_case_ids)  # take only common items
            elif filter_case_ids:  # if it is the first key
                case_ids = filter_case_ids  # (at first the set of cases is empty
                # => empty intersection as a result)

            if not case_ids:  # if the result set of case ids is empty after applying of the filter
                case_ids = set()  # then there is no element that satisfies the given filter conditions
                break  # and further iterations unnecessary
    print("Filters applied")
    '''

    # all variants (aggregated cases)
    variants = []
    # to each variant go identical cases,
    # so every variant is represented by one
    # case (its footprint)
    variants_footprints = []

    print("Start reading events...")
    cases = []
    if ct.Configs.DEBUG:
        for c in src.app.gen_test_cases():
            cases.append(c.id)
            found_idx = -1
            for var_idx, var_footprint in enumerate(variants_footprints):
                if c == var_footprint:
                    found_idx = var_idx

            if found_idx != -1:
                # check if the same case is already in variants
                for var_cid in variants[found_idx].cases:
                    if c.id == var_cid:
                        found_idx = -1
                    if found_idx != -1:
                        variants[found_idx].cases.append(c)
                        break
            else:
                variants_footprints.append(c)
                variants.append(Variant(c))
    else:
        if not ct.Configs.JXES:
            cases = []
            for idx, cid in enumerate(case_ids):  # FIXME DEBUG REMOVE IDX
                print(f"-- case {cid}\t nr. {idx + 1}\t out of {len(case_ids)}")
                c = Case(cid)
                c.events = mariadb_service.events(cid)
                cases.append(cid)

                found_idx = -1
                for var_idx, var_footprint in enumerate(variants_footprints):
                    if c == var_footprint:
                        found_idx = var_idx

                if found_idx != -1:
                    # check if the same case is already in variants
                    for var_cid in variants[found_idx].cases:
                        if cid == var_cid:
                            found_idx = -1
                        if found_idx != -1:
                            variants[found_idx].cases.append(c)
                            break
                else:
                    variants_footprints.append(c)
                    variants.append(Variant(c))

                # FIXME DEBUG
                if idx == ct.Configs.SIZE:
                    break
        else:
            # parse jxes to case-objects
            cases_json = json.loads(src.app.get_cases())["traces"]
            for idx, case_json in enumerate(cases_json):  # FIXME DEBUG REMOVE IDX
                cid = case_json["attrs"]["concept:name"]
                case = Case(cid)
                events = []
                for event_json in case_json["events"]:
                    e_name = event_json['concept:name']
                    event = Event(f"{e_name}_{cid}", e_name)
                    event.attributes = event_json
                    events.append(event)
                # sort events in a case
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

                # FIXME DEBUG
                if idx == ct.Configs.SIZE:
                    break


    print("Cases and variants are read out from database")

    return cases, variants
