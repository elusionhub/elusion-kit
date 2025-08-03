from elusion._core.authentication import BaseAuthenticator
from elusion._core.types import HeadersDict


class NoAuthAuthenticator(BaseAuthenticator):
    """No authentication required for the public Jokes API."""
    
    def get_auth_headers(self) -> HeadersDict:
        """No authentication headers needed for public API."""
        return {}
    
    def authenticate_request(self, headers: HeadersDict) -> HeadersDict:
        """Pass through headers without modification."""
        return headers