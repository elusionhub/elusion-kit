from enum import Enum
from typing import Union

JokeID = Union[int, str]


class JokeType(str, Enum):
    """Types of jokes available."""

    GENERAL = "general"
    PROGRAMMING = "programming"
    DAD = "dad"
    KNOCK_KNOCK = "knock-knock"


class JokeFormat(str, Enum):
    """Format of joke delivery."""

    SETUP_PUNCHLINE = "setup_punchline"
    SINGLE = "single"
    QUESTION_ANSWER = "question_answer"
