import traceback

'''
    Prints details of the passed error.
'''
def print_error(err):
    template = "\n--- An exception of type {0} occurred. Arguments:\n{1!r}"
    err_message = template.format(type(err).__name__, err.args)
    print(err_message)
    print("\n--- Traceback:\n" + traceback.format_exc())