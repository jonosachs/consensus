model_config = {
    "gemini": {
        "name": "gemini",
        "args": [
            "gemini",
            "--model",
            "flash-lite",
            "-p",
        ],
    },
    "claude": {"name": "claude", "args": ["claude", "-p"]},
    "codex": {
        "name": "codex",
        "args": ["codex", "exec", "--skip-git-repo-check", "--full-auto"],
    },
}
