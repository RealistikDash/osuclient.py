class InvalidBanchoTokenException(Exception):
    """Raised when no valid bancho session token is provided."""
    pass

class RejectedBanchoTokenException(Exception):
    """Raised when a bancho session token is rejected."""
    pass

class InvalidBanchoResponse(Exception):
    """Raised when bancho responds with a response code other than 200."""
    pass