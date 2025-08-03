from typing import Optional, List, Any, Dict
from pydantic import Field, field_validator

from elusion._core.base_models import BaseServiceModel
from .enum import JokeID


class Joke(BaseServiceModel):

    id: JokeID = Field(..., description="Unique identifier for the joke")
    type: Optional[str] = Field(None, description="Type/category of the joke")
    setup: str = Field(..., description="The setup/beginning of the joke")
    punchline: str = Field(..., description="The punchline/ending of the joke")

    @field_validator("setup", "punchline")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        """Ensure setup and punchline are not empty."""
        if not v or not v.strip():
            raise ValueError("Setup and punchline cannot be empty")
        return v.strip()

    def __str__(self) -> str:
        """String representation of the joke."""
        return f"{self.setup} - {self.punchline}"

    def __repr__(self) -> str:
        """Developer representation of the joke."""
        return f"Joke(id={self.id}, setup='{self.setup[:30]}...', punchline='{self.punchline[:30]}...')"

    def to_display_format(self) -> str:
        """Format joke for display."""
        return f"🎭 {self.setup}\n💥 {self.punchline}"

    def is_clean(self) -> bool:
        """Check if joke appears to be family-friendly (basic heuristic)."""
        # Simple check for potentially inappropriate content
        inappropriate_words = {"damn", "hell", "stupid", "idiot", "dumb", "crap"}
        text = f"{self.setup} {self.punchline}".lower()
        return not any(word in text for word in inappropriate_words)


class JokesList(BaseServiceModel):
    """A collection of jokes with metadata."""

    jokes: List[Joke] = Field(default_factory=list, description="List of jokes")
    count: int = Field(0, description="Total number of jokes")

    def __len__(self) -> int:
        """Get the number of jokes."""
        return len(self.jokes)

    def __getitem__(self, index: int) -> Joke:
        """Get joke by index."""
        return self.jokes[index]

    def filter_clean_jokes(self) -> "JokesList":
        """Get only family-friendly jokes."""
        clean_jokes = [joke for joke in self.jokes if joke.is_clean()]
        return JokesList(jokes=clean_jokes, count=len(clean_jokes))

    def filter_by_type(self, joke_type: str) -> "JokesList":
        """Filter jokes by type."""
        filtered_jokes = [joke for joke in self.jokes if joke.type and joke.type.lower() == joke_type.lower()]
        return JokesList(jokes=filtered_jokes, count=len(filtered_jokes))

    def random_joke(self) -> Optional[Joke]:
        """Get a random joke from the list."""
        if not self.jokes:
            return None

        import random

        return random.choice(self.jokes)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {"jokes": [joke.model_dump() for joke in self.jokes], "count": self.count}
