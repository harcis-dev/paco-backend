class Configs:
    LANGUAGE = 'E'

class Attributes:
    FREQUENCY = "frequency"

class ProcessModelLabels:
    START = ''
    END = ''

class EpcLabels:
    START = ''


def set_language(lang_str):
    if lang_str == 'E':
        Configs.LANGUAGE = 'E'

        ProcessModelLabels.START = 'Start'
        ProcessModelLabels.END = 'End'

        EpcLabels.START = 'Process started'
    elif lang_str == 'D':
        Configs.LANGUAGE = 'D'

        ProcessModelLabels.START = 'Start'
        ProcessModelLabels.END = 'Ende'

        EpcLabels.START = 'Prozess gestartet'
