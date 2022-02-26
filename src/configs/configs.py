class Configs:
    """
    A class with constants used to set global configurations.

    Attributes
    __________
    LANGUAGE : str
        A constant that represents the language of labels for all the models.
    """
    LANGUAGE = 'E'

    DEBUG = True
    SIZE = 1000


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
    START : str
        A constant that represents the start node label.
    EVENT : str
        A constant that represents the event node type.
    EVENT_LABEL : str
        A constant that represents the event node label addition.
    FUNCTION : str
        A constant that represents the function node type.
    FUNCTION : str
        A constant that represents the function preceding a split XOR operator.
    """
    START = ''
    EVENT = 'Event'
    START_LABEL = ''
    EVENT_LABEL = ''
    FUNCTION = 'Function'
    SPLIT_FUNCTION = ''


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

        EpcLabels.START = 'Start'
        EpcLabels.START_LABEL = 'Process started'
        EpcLabels.EVENT_LABEL = 'created'
        EpcLabels.SPLIT_FUNCTION = 'function'
    elif Configs.LANGUAGE == 'D':
        DfgLabels.START = 'Start'
        DfgLabels.END = 'Ende'

        EpcLabels.START = 'Start'
        EpcLabels.START_LABEL = 'Prozess gestartet'
        EpcLabels.EVENT_LABEL = 'erstellt'
        EpcLabels.SPLIT_FUNCTION = 'Funktion'
