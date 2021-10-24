from src.databases.mariadb_services import mariadb_service
from src.eventlog.eventlog import EventLog
from src.model.case import Case


class Filter:
    DEBITORS        = "KUNNR"
    CREDITORS       = "LIFNR"
    ACCOUNTS        = "HKONT"
    USERS           = "USNAM"
    FIXED_ASSETS    = "ANLN1"


class SapEventLog(EventLog):

    '''
        Reads data from MariaDB and initializes cases
    '''
    def read_data(self, filters):
        case_ids = set()

        # array of filters is None or empty
        if filters is None or not filters:
            case_ids = mariadb_service.all_cases()
        else:
            for filter in filters.keys():
                filter_case_ids = mariadb_service.filter_cases(filter, filters[filter])
                if filter_case_ids and case_ids:
                    case_ids = case_ids.intersection(filter_case_ids)  # take only common items
                elif filter_case_ids:               # if it is the first key
                    case_ids = filter_case_ids  # (at first the set of cases is empty
                                                        # => empty intersection as a result)

                if not case_ids:      # if the result set of case ids is empty after applying of the filter
                    case_ids = set()  # then there is no element that satisfies the given filter conditions
                    break                 # and further iterations unnecessary

        cases = []
        for sid in case_ids:
            s = Case(sid)
            s.events = mariadb_service.events(sid)
            cases.append(sid)

        self.cases = cases
