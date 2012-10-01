class Error(Exception):
    """Error"""

def todo_error_handling(error_happened=True):
    if error_happened:
        raise Exception('Error happened. (TODO: Proper error handling)')
