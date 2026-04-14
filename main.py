from rich.console import Console
from instructions import instructions
from datetime import datetime
from config import model_config
from json import JSONDecodeError
import subprocess
import json
import os

history = []


def init():
    pass


def callLlm(model_config: dict, prompt: str):
    model_args = model_config["args"] + [prompt]
    run_settings = {"capture_output": True, "text": True}

    response = subprocess.run(model_args, **run_settings, timeout=30)
    output = response.stdout or response.stderr

    try:
        normd = normaliseResp(output)
        output_json = json.loads(normd)
        return output_json

    except JSONDecodeError as e:
        print(f"Malformed response: {output} {e}")
        raise JSONDecodeError(f"Error {e}", "", 0)


def update_history(response):
    model, text, done = deconstruct(response)
    history.append(
        {"assistant": {"name": model, "text": f"[{model}] {text}", "done": done}}
    )


def normaliseResp(response):
    normd = response.replace("```", "").replace("json", "")
    return normd


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
                print(history[-1]["assistant"]["text"])
                linebreak()


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
    console = Console()
    userin = ""
    history.append({"Datetime": now})
    history.append({"Instructions": instructions})

    while True:
        userin += input("query>")
        if userin.endswith("quit") or userin.endswith("exit"):
            break
        if userin.endswith("/"):
            linebreak()
            with console.status(
                "[bold green]Thinking...[/bold green]\n", spinner="dots"
            ):
                prompt = userin[:-1]
                runQuery(prompt)
                userin = ""

    if len(history) > 2:
        os.makedirs("logs", exist_ok=True)

        with open(f"logs/session{now}.json", "w") as f:
            json.dump(history, f, indent=4)


run()
