class CustomExceptions:
    """
    Collection of custom exceptions for more robust error handling.
    """

    class FailedDatabaseInit(Exception):
        """
        Exception thrown when database not found.
        """

        def __init__(self, details=None):
            super().__init__("Couldn't find database")
            self.details = details
