from rich.console import Console
from instructions import instructions
from datetime import datetime
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


def log_session(history, time):
    if len(history) > 3:
        os.makedirs("logs", exist_ok=True)
        with open(f"logs/session{time}.json", "w") as f:
            json.dump(history, f, indent=4)


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


def callLlm(config: dict, user_prompt: str) -> dict:
    model_name = config["name"]
    model_args = config["args"] + [user_prompt]

    try:
        with console.status("[bold green]Thinking...[/bold green]\n", spinner="dots"):
            response = run_subprocess(model_args)

        normal = normalise_resp(model_name, response)
        assert isinstance(normal, dict)
        return normal
    except OSError as e:
        logger.error(f"Error: {e}")
        return build_response(model_name, str(e))
    except subprocess.TimeoutExpired as e:
        return build_response(model_name, "Timed out.")
    except subprocess.CalledProcessError as e:
        return build_response(model_name, f"Command {e.cmd} failed")


def update_history(history: list, model: str, response: dict):
    text, done = deconstruct(response)
    struct_entry = build_response(model, text, done)
    history.append({"assistant": struct_entry})
    return history


def build_response(model: str, text: str, done: bool = True):
    return {"name": model, "text": text, "done": done}


def normalise_resp(model: str, response: str | dict) -> dict:
    if isinstance(response, str):
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

        # Should now be structured string
        try:
            return json.loads(response)
        except JSONDecodeError as e:
            # Otherwise likely plain text
            logger.info("Plain text response detected")
            return build_response(model, str(response))

    # Attempt to find text if not in "text" field, fall back to raw response
    if isinstance(response, dict):
        text = (
            response.get("text")
            or response.get("message")
            or response.get("result")
            or response.get("content")
            or str(response)
        )
        done = response.get("done", True)
        return build_response(model, text, done)

    # Unexpected format
    logger.warning("Unexpected response format")
    return build_response(model, str(response))


def run_query(history, user_prompt):
    history.append({"user": user_prompt.strip()})
    finished = {}
    for model in model_config:
        finished[model] = False

    for _ in range(5):
        for model in model_config:
            if not finished[model]:
                response = callLlm(
                    model_config[model], user_prompt=json.dumps(history, indent=4)
                )
                history = update_history(history, model, response)

                last_msg = history[-1]["assistant"]
                console.print(
                    f"[bold green]\\[{model}][/bold green] {last_msg['text']}\n"
                )
                if last_msg["done"]:
                    finished[model] = True

    return history


def deconstruct(response: dict) -> tuple:
    text = response.get("text", "")
    done = response.get("done", False)

    return text, done


def linebreak():
    console.print("")


def init_history(session_date):
    history = []
    history.append("Group Chat")
    history.append(f"Date: {session_date}")
    history.append(f"Instructions: {instructions}")
    history.append("Chat transcript starts below:")
    return history


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


def run():
    session_date = datetime.now().astimezone().isoformat()
    history = init_history(session_date)

    # Log session on crash
    sys.excepthook = lambda typ, val, tb: (
        log_session(history, session_date),
        # Propagate crash details
        sys.__excepthook__(typ, val, tb),
    )

    linebreak()
    while True:
        userp = get_prompt()
        if userp == "exit":
            break
        linebreak()
        history = run_query(history, userp)

    if len(history) > 3:
        log_session(history, session_date)


run()
