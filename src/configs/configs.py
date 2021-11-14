class Configs:
    LANGUAGE = 'E'

class Attributes:
    FREQUENCY = "frequency"

class ProcessModelLabels:
    START = ''
    END = ''

class EpcLabels:
    START = ''
    EVENT = ''
    EVENT_LABEL = ''
    FUNCTION = ''


def set_language(lang_str):
    if lang_str == 'E':
        Configs.LANGUAGE = 'E'

        ProcessModelLabels.START = 'Start'
        ProcessModelLabels.END = 'End'

        EpcLabels.START = 'Start'
        EpcLabels.EVENT = 'Event'
        EpcLabels.EVENT_LABEL = 'created'
        EpcLabels.FUNCTION = 'Function'
    elif lang_str == 'D':
        Configs.LANGUAGE = 'D'

        ProcessModelLabels.START = 'Start'
        ProcessModelLabels.END = 'Ende'

        EpcLabels.START = 'Start'
        EpcLabels.EVENT = 'Eregnis'
        EpcLabels.EVENT_LABEL = 'erstellt'
        EpcLabels.FUNCTION = 'Funktion'
