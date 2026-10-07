class AuthError(Exception):
    def __init__(self, message, status=400, envelope="error"):
        super().__init__(message)
        self.status = status
        self.envelope = envelope
