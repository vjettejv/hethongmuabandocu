class LegacyError(Exception):
    def __init__(self, message, status=500):
        super().__init__(message)
        self.status = status
