from typing import Optional, List

from elusion._core.base_client import BaseResource
from .models import Joke
from .enum import JokeID
from .exceptions import JokesNotFoundError, JokesAPIError


class JokesResource(BaseResource):
    """Resource for managing joke operations.
    
    Provides methods for fetching jokes from the Sample APIs Jokes service.
    """
    
    def get_good_jokes(self, limit: Optional[int] = None) -> List[Joke]:
        """Get a list of good jokes.
        
        Args:
            limit: Maximum number of jokes to return (client-side limit)
            
        Returns:
            List of jokes
            
        Raises:
            JokesAPIError: If the API request fails
            JokesServiceUnavailableError: If the service is unavailable
        """
        try:
            response = self._http_client.get("/jokes/goodJokes")
            
            # Parse the response data
            jokes_data = response.json()
            
            # Handle different response formats
            if isinstance(jokes_data, list):
                jokes = [Joke.model_validate(joke_data) for joke_data in jokes_data]
            else:
                # If API returns a different format, adapt accordingly
                raise JokesAPIError(
                    message="Unexpected response format from jokes API",
                    service_name="SampleAPIsJokes",
                    status_code=response.status_code
                )
            
            # Apply client-side limit if specified
            if limit is not None and limit > 0:
                jokes = jokes[:limit]
            
            return jokes
            
        except Exception as e:
            if isinstance(e, JokesAPIError):
                raise
            
            # Wrap other exceptions in our custom exception
            raise JokesAPIError(
                message=f"Failed to fetch jokes: {str(e)}",
                service_name="SampleAPIsJokes"
            ) from e
    
    def get_joke_by_id(self, joke_id: JokeID) -> Joke:
        """Get a specific joke by ID.
        
        Note: The Sample APIs Jokes service doesn't support fetching by ID,
        so this method fetches all jokes and finds the one with matching ID.
        
        Args:
            joke_id: ID of the joke to fetch
            
        Returns:
            The requested joke
            
        Raises:
            JokesNotFoundError: If joke with given ID is not found
            JokesAPIError: If the API request fails
        """
        jokes = self.get_good_jokes()
        
        # Find joke with matching ID
        for joke in jokes:
            if str(joke.id) == str(joke_id):
                return joke
        
        # Joke not found
        raise JokesNotFoundError(
            resource_type="Joke",
            resource_id=str(joke_id)
        )
    
    def get_random_joke(self) -> Joke:
        """Get a random joke.
        
        Returns:
            A random joke from the collection
            
        Raises:
            JokesAPIError: If no jokes are available or API fails
        """
        jokes = self.get_good_jokes()
        
        if not jokes:
            raise JokesAPIError(
                message="No jokes available",
                service_name="SampleAPIsJokes"
            )
        
        import random
        return random.choice(jokes)
    
    def search_jokes(self, query: str, limit: Optional[int] = None) -> List[Joke]:
        """Search for jokes containing specific text.
        
        Args:
            query: Search query (searches in setup and punchline)
            limit: Maximum number of results to return
            
        Returns:
            List of jokes matching the search query
        """
        jokes = self.get_good_jokes()
        query_lower = query.lower()
        
        # Filter jokes that contain the query in setup or punchline
        matching_jokes = [
            joke for joke in jokes
            if query_lower in joke.setup.lower() or query_lower in joke.punchline.lower()
        ]
        
        # Apply limit if specified
        if limit is not None and limit > 0:
            matching_jokes = matching_jokes[:limit]
        
        return matching_jokes
    
    def get_clean_jokes(self, limit: Optional[int] = None) -> List[Joke]:
        """Get family-friendly jokes only.
        
        Args:
            limit: Maximum number of jokes to return
            
        Returns:
            List of clean jokes
        """
        jokes = self.get_good_jokes()
        clean_jokes = [joke for joke in jokes if joke.is_clean()]
        
        if limit is not None and limit > 0:
            clean_jokes = clean_jokes[:limit]
        
        return clean_jokes