from datetime import datetime
from instructions import instructions as default_instruct
from dataclasses import dataclass


@dataclass
class Message:
    role: str
    name: str
    text: str
    done: bool = True


class Session:
    def __init__(
        self,
        title="Group Chat",
        instructions=None,
    ) -> None:
        self._title = title
        self._session_date = datetime.now().astimezone().isoformat()
        self._instructions = instructions or default_instruct
        self._transcript: list[Message] = []

    def add_prompt(self, text: str) -> None:
        self._transcript.append(Message("user", "prompt", text))

    def add_response(self, message: Message):
        self._transcript.append(message)

    def get_lastmsg(self) -> Message | None:
        if self._transcript:
            return self._transcript[-1]
        return None

    def get_instructions(self) -> str:
        return self._instructions

    def get_transcript(self) -> list[Message]:
        return self._transcript

    def get_window(self, n: int) -> list[Message]:
        if len(self._transcript) > abs(n):
            return self._transcript[n:]
        return self._transcript

    def get_date(self) -> str:
        return self._session_date

    def length(self) -> int:
        return len(self._transcript)

    def to_dict(self) -> dict:
        return {
            "title": self._title,
            "session_date": self._session_date,
            "instructions": self._instructions,
            "transcript": [vars(msg) for msg in self._transcript],
        }
