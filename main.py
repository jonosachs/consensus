from types import UnionType
from rich.console import Console
from instructions import instructions
from datetime import datetime
from config import model_config
from json import JSONDecodeError
import subprocess
import json
import os
import logging

history = []
console = Console()
logger = logging.getLogger(__name__)


def run_subprocess(args, timeout: int = 30) -> dict | str:
    response = subprocess.run(
        args, capture_output=True, text=True, check=True, timeout=timeout
    )
    return response.stdout


def callLlm(model_config: dict, prompt: str) -> dict:
    model_name = model_config["name"]
    model_args = model_config["args"] + [prompt]

    try:
        with console.status("[bold green]Thinking...[/bold green]\n", spinner="dots"):
            response = run_subprocess(model_args)

        normal = normalise_resp(model_name, response)
        logger.info(f"Normalised response: {normal}")
        return normal
    except OSError as e:
        logger.error(f"Error: {e}")
        return build_response(model_name, str(e))
    except subprocess.TimeoutExpired as e:
        return build_response(model_name, "Timed out.")


def update_history(model: str, response: dict):
    text, done = deconstruct(response)
    struct_entry = build_response(model, text, done)
    history.append({"assistant": struct_entry})


def build_response(model: str, text: str, done: bool = True):
    return {"name": model, "text": text, "done": done}


def normalise_resp(model: str, response: str | dict) -> dict:
    # String with markdown
    if isinstance(response, str) and "```" in response:
        response = response.replace("```", "").replace("json", "").strip()

    # If structured string convert to dict
    if isinstance(response, str):
        try:
            return json.loads(response)
        except JSONDecodeError as e:
            # Otherwise likely unstructured string
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
        return build_response(model, text)

    # Unexpected format
    return build_response(model, str(response))


def runQuery(prompt):
    history.append({"user": prompt.strip()})
    finished = {}
    for model in model_config:
        finished[model] = False

    for _ in range(2):
        for model in model_config:
            if not finished[model]:
                response = callLlm(
                    model_config[model], prompt=json.dumps(history, indent=4)
                )
                update_history(model, response)

                if history[-1]["assistant"]["done"]:
                    finished[model] = True

                last_msg = history[-1]["assistant"]["text"]
                print(f"[{model}] {last_msg}\n")


def deconstruct(response: dict) -> tuple:
    text = response.get("text", "")
    done = response.get("done", False)

    return text, done


def linebreak():
    print("")


def run():
    now = datetime.now().astimezone().isoformat()
    userin = ""
    history.append({"Datetime": now})
    history.append({"Instructions": instructions})

    while True:
        userin += input("query>")
        if userin.endswith("quit") or userin.endswith("exit"):
            break
        if userin.endswith("/"):
            linebreak()
            prompt = userin[:-1]
            runQuery(prompt)
            userin = ""

    if len(history) > 2:
        os.makedirs("logs", exist_ok=True)

        with open(f"logs/session{now}.json", "w") as f:
            json.dump(history, f, indent=4)


run()
