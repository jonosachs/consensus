from rich.console import Console
from instructions import instructions
from datetime import datetime
from config import model_config
from json import JSONDecodeError
import subprocess
import json
import os

history = []
console = Console()


def run_subprocess(args, timeout=30):
    response = subprocess.run(
        args, capture_output=True, text=True, check=True, timeout=timeout
    )
    return response.stdout


def callLlm(model_config: dict, prompt: str):
    model_name = model_config["name"]
    model_args = model_config["args"] + [prompt]

    try:
        with console.status("[bold green]Thinking...[/bold green]\n", spinner="dots"):
            response = run_subprocess(model_args)

        normal = normalise_resp(model_name, response)
        return normal
    except OSError as e:
        print(f"Error: {e}")
        return build_response(model_name, str(e))
    except subprocess.TimeoutExpired as e:
        return build_response(model_name, "Timed out.")


def update_history(response):
    model, text, done = deconstruct(response)
    structured = build_response(model, text, done)
    history.append({"assistant": structured})


def build_response(model, text, done=True):
    return {"name": model, "text": text, "done": done}


def normalise_resp(model, response=str | dict) -> dict:
    # String with markdown
    if isinstance(response, str) and "```" in response:
        response = response.replace("```", "").replace("json", "").strip()

    # Still string (may be plain text)
    if isinstance(response, str):
        try:
            return json.loads(response)
        except JSONDecodeError as e:
            print(f"Malformed json: {str(response)}")
            return build_response(model, f"JSON error: {str(e)}")

    # Attempt to find text response if not in "text" field, fall back to response
    if isinstance(response, dict):
        text = (
            response["text"]
            or response["message"]
            or response["result"]
            or response["content"]
            or str(response)
        )
        return build_response(model, text)

    return response


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
                update_history(response)

                if history[-1]["assistant"]["done"]:
                    finished[model] = True

                last_msg = history[-1]["assistant"]["text"]
                print(f"[{model}] {last_msg}\n")


def deconstruct(response):
    model = response.get("name", "")
    text = response.get("text", "")
    done = response.get("done", False)

    if not model or not text:
        print(f"LLM response appears malformed: {response}")
        return "", "", ""

    return model, text, done


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
