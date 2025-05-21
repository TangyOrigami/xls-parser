class FailedDatabaseInit(BaseException):
    """
    Exception thrown when database not found.
    """

    def __init__(self, details=None):
        super().__init__("Couldn't find database")
        self.details = details


class NoWorkEntries(BaseException):
    """
    Exception thrown when database not found.
    """

    def __init__(self, details=None):
        super().__init__("No work entries were found")
        self.details = details
