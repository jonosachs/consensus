from models import Message, Session
from rich.console import Console
from instructions import instructions
from config import model_config
from json import JSONDecodeError
from prompt_toolkit import prompt
import subprocess
import json
import os
import logging
import atexit
import sys

console = Console()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def log_session(session: Session):
    os.makedirs("logs", exist_ok=True)
    with open(f"logs/session{session.get_date()}.json", "w") as f:
        json.dump(session.to_dict(), f, indent=4)


def cleanup():
    # Restore terminal to sane (sensible) defaults
    subprocess.run(["stty", "sane"])


# Register cleanup function to run on exit or unhandled exception
atexit.register(cleanup)


def run_subprocess(args, timeout: int = 45) -> str:
    response = subprocess.run(
        args, capture_output=True, text=True, check=True, timeout=timeout
    )
    return response.stdout


def callLlm(config: dict, user_prompt: str) -> str:
    model_args = config["args"] + [user_prompt]

    try:
        with console.status("[bold green]Thinking...[/bold green]\n", spinner="dots"):
            response = run_subprocess(model_args)
        return response
    except OSError as e:
        logger.error(f"Error: {e}")
        return str(e)
    except subprocess.TimeoutExpired as e:
        return "Timed out."
    except subprocess.CalledProcessError as e:
        return f"Command {e.cmd} failed"


def build_response(role: str, model: str, text: str, done: bool = True):
    return Message(role, model, text, done)


def normalise(model: str, response: str) -> Message:
    response = response.strip()

    # String with markdown (typically fenced code block)
    if response.startswith("```json") and response.endswith("```"):
        logger.info("Removing fencing and json tag from response")
        response = response.removeprefix("```json").removesuffix("```").strip()

    # Response includes text outside curly braces
    lead_or_trail = not response.startswith("{") or not response.endswith("}")
    has_curly = "{" in response and "}" in response
    if lead_or_trail and has_curly:
        logger.info("Text found outside curly braces")
        start = response.find("{")
        end = response.rfind("}") + 1
        response = response[start:end].strip()

    # Should now be JSON structured string
    try:
        r = json.loads(response)
        text, done = r.values()
        return build_response("assistant", model, text, done)
    except JSONDecodeError as e:
        # Otherwise likely plain text
        logger.info("Plain text response detected")
        return build_response("assistant", model, str(response), True)


def collect_responses(session: Session):
    participants = [model for model in model_config]

    for _ in range(5):
        for model in participants.copy():
            response = callLlm(
                model_config[model],
                user_prompt=json.dumps(session.to_dict(), indent=4),
            )
            msg = normalise(model, response)
            session.add_response(msg)
            last = session.get_lastmsg()

            if last:
                console.print(f"[bold green]\\[{model}][/bold green] {last.text}\n")
                if last.done:
                    participants.remove(model)
            else:
                logger.warning(f"None type response from {model}")

            if not participants:
                break

    return session


def deconstruct(response: dict) -> tuple:
    text = response.get("text", "")
    done = response.get("done", False)

    return text, done


def linebreak():
    console.print("")


def handle_quit(userp):
    if userp.lower().strip() == "quit" or userp.lower().strip() == "exit":
        return "exit"

    # User typed exit/quit on a new line
    start = userp.rfind("\n") + 1
    after_lb = userp[start:]
    if after_lb == "quit" or after_lb == "exit":
        return "exit"

    # Otherwise assume quit/exit was used in dif context
    return userp


def get_prompt():
    userin = ""
    while True:
        userin += prompt("query> ") + "\n"
        if userin.strip().endswith("/"):
            user_prompt = userin.rstrip("\n").rstrip("/")
            if "quit" in user_prompt or "exit" in user_prompt:
                user_prompt = handle_quit(user_prompt)
            userin = ""
            return user_prompt


def setup_crashlogging(session):
    # Log session on crash
    sys.excepthook = lambda typ, val, tb: (
        log_session(session),
        # Propagate crash details
        sys.__excepthook__(typ, val, tb),
    )


def run():
    session = Session()
    setup_crashlogging(session)

    linebreak()
    while True:
        user_prmt = get_prompt()
        if user_prmt == "exit":
            break
        linebreak()
        session.add_prompt(user_prmt)
        session = collect_responses(session)

    if session.length() > 3:
        log_session(session)


if __name__ == "__main__":
    run()
