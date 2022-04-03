import traceback

'''
    Prints details of the passed error.
'''
def print_error(err):
    template = "\n--- An exception of type {0} occurred. Arguments:\n{1!r}"
    err_message = template.format(type(err).__name__, err.args)
    print(err_message)
    print("\n--- Traceback:\n" + traceback.format_exc())

    # Logging
    import logging
    import os
    log_filename = "paco_logs/paco_debug.log"
    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    logging.FileHandler(log_filename, mode="w", encoding=None, delay=False)
    logging.basicConfig(filename="paco_logs/paco_debug.log", level=logging.DEBUG)
    logging.debug(f"\nerror: {err_message}\ntraceback: {traceback.format_exc()}")
    # -----------
