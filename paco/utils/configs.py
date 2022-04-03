class Configs:
    """
    A class with constants used to set global configurations.

    Attributes
    __________
    LANGUAGE : str
        A constant that represents the language of labels for all the models.
    """
    LANGUAGE = 'E'

    JXES = False
    DEBUG = False and not JXES
    EPC_EXAMP = True and DEBUG
    DEBUG_CASES = "AND_SMALL"
    REPRODUCIBLE = False and not DEBUG and not JXES
    SIZE = 1000


class Errcodes:
    """
    A class with constant codes of errors that can occur during the graph creation.

    '''
    Attributes
    __________
    UNEXPECTED_ERROR : int
        An error code indicating that the raised exception was not expected.
    JXES_NO_CONNECTION : int
        An error code indicating that the data extraction system has not been started or is not reachable.
    MARIADB_NO_CONNECTION : int
        An error code indicating that MariaDB has not been started or is not reachable.
    MARIADB_NO_DATA : int
        An error code indicating that MariaDB does not contain the necessary tables, columns or entries.
    MONGODB_NO_CONNECTION
        An error code indicating that MongoDB has not been started or is not reachable.
    MONGODB_UPSERT_ERROR
        An error code indicating that the graph could not be inserted into MongoDB.
    ERR_SUFFIX_CONNECTION : str
        Ending of the error messages which indicate problems in establishing a connection.
    ERR_MESSAGES : dict
        Error messages for each error code.
    """
    UNEXPECTED_ERROR = -1
    JXES_NO_CONNECTION = 1
    MARIADB_NO_CONNECTION = 2
    MARIADB_NO_DATA = 3
    MONGODB_NO_CONNECTION = 4
    MONGODB_UPSERT_ERROR = 5

    ERR_SUFFIX_CONNECTION = " has not been started or is not reachable."
    ERR_SUFFIX_DATA = " does not contain the necessary data to create graphs."

    ERR_MESSAGES = {
                    UNEXPECTED_ERROR: "An unexpected application error occurred.",
                    JXES_NO_CONNECTION: "Data extraction system"+ERR_SUFFIX_CONNECTION,
                    MARIADB_NO_CONNECTION: "MariaDB"+ERR_SUFFIX_CONNECTION,
                    MARIADB_NO_DATA: "MariaDB"+ERR_SUFFIX_DATA,
                    MONGODB_NO_CONNECTION: "MongoDB"+ERR_SUFFIX_CONNECTION,
                    MONGODB_UPSERT_ERROR: "Graphs could not be inserted into MongoDB."}

    curr_errcode = 0

class Attributes:
    """
    A class with constants that represent event attributes.

    '''
    Attributes
    __________
    FREQUENCY : str
        A constant that represents the attribute name 'frequency'.
    """
    FREQUENCY = "frequency"


class DfgLabels:
    """A class with constants that represent common dfg labels.

    The constants will be set in `paco.utils.configs.set_language`.

    Attributes
    __________
    START : str
        A constant that represents the start node label.
    END : str
        A constant that represents the end node label.
    """
    START = 'Start'
    END = 'End'

class BasisLabels:
    """A class with constants that represent abstract basis graph labels.

    The constants should be translated into the corresponding graph type notation.

    Attributes
    __________
    NODE : str
        A constant that represents the abstract node type.
    """
    NODE = 'node'

class EpcLabels:
    """A class with constants that represent common epc labels.

    The constants will be defined via `paco.utils.configs.set_labels_language` in `paco.utils.configs.set_language`.

    Attributes
    __________
    START_LABEL : str
        A constant that represents the start node label.
    EVENT : str
        A constant that represents the event node type.
    EVENT_LABEL : str
        A constant that represents the event node label addition.
    XOR : str
        A constant that represents the xor operator type.
    FUNCTION : str
        A constant that represents the function node type.
    EDGE : str
        A constant that represents the edge type.
    FUNCTION : str
        A constant that represents the function preceding a split XOR operator.
    """
    START_LABEL = ''
    EVENT = 'Event'
    EVENT_LABEL = ''
    XOR = 'XOR'
    FUNCTION = 'Function'
    EDGE = 'InformationFlow'
    SPLIT_FUNCTION = ''

class BpmnLabels:
    """A class with constants that represent common bpmn labels.

    The constants will be defined via `paco.utils.configs.set_labels_language` in `paco.utils.configs.set_language`.

    Attributes
    __________
    PROCESS : str
        A constant that represents the process pool id.
    START : str
        A constant that represents the start event type.
    END : str
        A constant that represents the end event type.
    XOR : str
        A constant that represents the xor operator type.
    EDGE : str
        A constant that represents the edge type.
    ACTIVITY : str
        A constant that represents the activity node type.
    ACTIVITY_LABEL : str
        A constant that represents the activity node label addition.
    """
    PROCESS = 'Process'
    START = 'Intermediate'
    END = 'End'
    XOR = 'Exclusive'
    EDGE = 'StandardEdge'
    ACTIVITY = 'GenericTask'
    ACTIVITY_LABEL = ''


'''
    Node types, that should be merged.
'''
NODE_TYPES = [BasisLabels.NODE, EpcLabels.EVENT, EpcLabels.FUNCTION, BpmnLabels.ACTIVITY]


def set_language(lang_str):
    """Sets `paco.utils.configs.Configs.LANGUAGE` and invokes other language setting methods.

    Parameters
    ----------
    lang_str : str
        Language to be set. Options: 'E', 'D'.

    See Also
    --------
    paco.utils.configs.Configs
    """

    Configs.LANGUAGE = lang_str

    set_labels_language()


def set_labels_language():
    """Sets model labels in the language specified with `paco.utils.configs.Configs.LANGUAGE`.

    Parameters
    ----------
    lang_srt : str
        Language to be set. Options: 'E', 'D'.

    See Also
    --------
    paco.utils.configs.Configs
    paco.utils.configs.set_language
    """

    if Configs.LANGUAGE == 'E':
        DfgLabels.START = 'Start'
        DfgLabels.END = 'End'

        EpcLabels.START_LABEL = 'Process started'
        EpcLabels.EVENT_LABEL = 'created'
        EpcLabels.SPLIT_FUNCTION = 'function'

        BpmnLabels.ACTIVITY_LABEL = 'create'

    elif Configs.LANGUAGE == 'D':
        DfgLabels.START = 'Start'
        DfgLabels.END = 'Ende'

        EpcLabels.START_LABEL = 'Prozess gestartet'
        EpcLabels.EVENT_LABEL = 'erstellt'
        EpcLabels.SPLIT_FUNCTION = 'Funktion'

        BpmnLabels.ACTIVITY_LABEL = 'erstellen'
