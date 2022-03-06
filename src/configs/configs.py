class Configs:
    """
    A class with constants used to set global configurations.

    Attributes
    __________
    LANGUAGE : str
        A constant that represents the language of labels for all the models.
    """
    LANGUAGE = 'E'

    DEBUG = False
    DEBUG_CASES = "EPC"
    REPRODUCIBLE = False
    JXES = False
    SIZE = 2000


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

    The constants will be set in `src.configs.configs.set_language`.

    Attributes
    __________
    START : str
        A constant that represents the start node label.
    END : str
        A constant that represents the end node label.
    """
    START = 'Start'
    END = 'End'


class EpcLabels:
    """A class with constants that represent common epc labels.

    The constants will be defined via `src.configs.configs.set_labels_language` in `src.configs.configs.set_language`.

    Attributes
    __________
    START_LABEL : str
        A constant that represents the start node label.
    EVENT : str
        A constant that represents the event node type.
    EVENT_LABEL : str
        A constant that represents the event node label addition.
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
    FUNCTION = 'Function'
    EDGE = 'InformationFlow'
    SPLIT_FUNCTION = ''

class BpmnLabels:
    """A class with constants that represent common bpmn labels.

    The constants will be defined via `src.configs.configs.set_labels_language` in `src.configs.configs.set_language`.

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


def set_language(lang_str):
    """Sets `src.configs.configs.Configs.LANGUAGE` and invokes other language setting methods.

    Parameters
    ----------
    lang_str : str
        Language to be set. Options: 'E', 'D'.

    See Also
    --------
    src.configs.configs.Configs
    """

    Configs.LANGUAGE = lang_str

    set_labels_language()


def set_labels_language():
    """Sets model labels in the language specified with `src.configs.configs.Configs.LANGUAGE`.

    Parameters
    ----------
    lang_srt : str
        Language to be set. Options: 'E', 'D'.

    See Also
    --------
    src.configs.configs.Configs
    src.configs.configs.set_language
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
