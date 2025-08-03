from typing import Optional

from elusion._core.base_client import BaseServiceClient
from elusion._core.configuration import ClientConfiguration, ServiceSettings
from .authentication import NoAuthAuthenticator
from .jokes_resource import JokesResource


class JokesSDK(BaseServiceClient):
    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        debug: bool = False,
    ):
        config = ClientConfiguration(
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            debug_requests=debug,
            user_agent="elusion-jokes-sdk/1.0.0",
        )

        service_settings = ServiceSettings(
            base_url=base_url or "https://api.sampleapis.com",
            api_version=None,  # No versioning in this API
            service_specific_config={
                "public_api": True,
                "rate_limit": None,
            },
        )

        authenticator = NoAuthAuthenticator()

        super().__init__(
            config=config,
            service_settings=service_settings,
            authenticator=authenticator,
        )

        self.jokes = JokesResource(self._http_client)

    def _get_service_name(self) -> str:
        """Get the service name."""
        return "SampleAPIsJokes"

    def _get_base_url(self) -> str:
        """Get the base URL for the Jokes API."""
        return "https://api.sampleapis.com"

    def test_connection(self) -> bool:
        """Test the connection to the Jokes API.

        Returns:
            True if the API is accessible
        """
        try:
            # Try to get a small number of jokes to test connectivity
            jokes = self.jokes.get_good_jokes(limit=1)
            return len(jokes) >= 0  # Even empty list means API is working
        except Exception:
            return False
