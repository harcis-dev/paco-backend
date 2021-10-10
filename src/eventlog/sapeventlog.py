from src.databases.mariadb_services import mariadb_service
from src.eventlog.eventlog import EventLog
from src.model.sequence import Sequence


class Filter:
    DEBITORS        = "KUNNR"
    CREDITORS       = "LIFNR"
    ACCOUNTS        = "HKONT"
    USERS           = "USNAM"
    FIXED_ASSETS    = "ANLN1"


class SapEventLog(EventLog):

    '''
        Reads data from MariaDB and initializes sequences
    '''
    def read_data(self, filters):
        sequence_ids = set()

        # array of filters is None or empty
        if filters is None or not filters:
            sequence_ids = mariadb_service.all_sequences()
        else:
            for filter in filters.keys():
                filter_sequence_ids = mariadb_service.filter_sequences(filter, filters[filter])
                if filter_sequence_ids and sequence_ids:
                    sequence_ids = sequence_ids.intersection(filter_sequence_ids)  # take only common items
                    if not sequence_ids:  # if there were no common items => all the following intersections will be empty
                        break             # => further iterations unnecessary
                elif filter_sequence_ids:               # if it is the first key
                    sequence_ids = filter_sequence_ids  # (at first the set of sequences is empty
                                                        # => empty intersection as a result)
                else:                     # if the set of sequence ids for the current filter is empty
                    sequence_ids = set()  # then there is no element that satisfies the given filter conditions
                    break                 # => further iterations unnecessary

        sequences = []
        for sid in sequence_ids:
            s = Sequence(sid)
            s.events = mariadb_service.events(sid)
            sequences.append(sid)

        self.sequences = sequences
