
class Error(Exception):
    """
    Generic module exception
    """


class StateNotReached(Error):
    """
    An state that was expected to be reached could not be reached
    in the allocated time
    """
