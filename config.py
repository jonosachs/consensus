model_config = {
    "gemini": {
        "args": [
            "gemini",
            "--model",
            "flash-lite",
            "-p",
        ]
    },
    "claude": {"args": ["claude", "-p"]},
    "codex": {
        "args": ["codex", "exec", "--skip-git-repo-check", "--full-auto"],
    },
}
