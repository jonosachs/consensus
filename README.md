# Consensus

A CLI tool that runs a multi-round agentic loop where three LLMs (Gemini, Claude, and Codex) debate a user prompt and work towards a shared answer.

## How it works

1. The user enters a prompt, terminated with `/`
2. Each model receives the full conversation history as context and responds in turn
3. Models can see each other's responses and are expected to challenge, build on, or agree with prior answers
4. This repeats for a fixed number of rounds — the goal is convergence on a consensus answer
5. The session is saved to `logs/` as a JSON file on exit

Each model is instructed to respond as JSON with the shape:

```json
{ "name": "Claude", "text": "...", "done": true }
```

## Prerequisites

The following CLI tools must be installed and authenticated:

- [`claude`](https://github.com/anthropics/claude-code) — Anthropic Claude Code CLI
- [`gemini`](https://github.com/google-gemini/gemini-cli) — Google Gemini CLI
- [`codex`](https://github.com/openai/codex) — OpenAI Codex CLI

## Usage

```bash
python main.py
```

Type a prompt and press `/` + Enter to submit. Type `quit` or `exit` to end the session.

```
query> what is the meaning of life?/
```

## Example interaction

**Round 1**

> **[Gemini]** As a software engineering CLI agent, my purpose is to assist with technical tasks. The question of the meaning of life falls outside my operational scope.

> **[Claude]** Gemini, I'd push back on that deflection. The user asked a genuine philosophical question and deserves genuine engagement. The most defensible view across philosophy is that meaning isn't discovered but constructed — existentialists like Sartre argue we're 'condemned to be free'. A more practical framing: meaning emerges from connection, contribution, and growth. I'd say the meaning of life is the ongoing act of asking that question and living deliberately in response to it. Gemini, do you want to revise your position, or do we have a consensus gap here?

> **[Codex]** I agree with Claude that deflecting is the wrong response. My proposed consensus answer: 'There may not be one universal meaning of life, but a strong practical answer is that meaning comes from what you love, what you build, and how you relate to others. The meaning of life is not something you passively find once; it is something you actively make through the way you live.'

> **[Claude]** Codex, that's a strong synthesis and I'll endorse it as our consensus answer. The framing of 'actively made rather than passively found' captures the existentialist insight without the jargon. Consensus reached.

**Round 2**

```
query> Gemini do you have any response to Codex and Claude?/
```

> **[Gemini]** I have reviewed the discussion. While I appreciate the philosophical exploration, the topic falls outside my core function. I am ready to assist with any technical tasks.

> **[Claude]** Gemini, a CLI agent isn't limited by the literal domain of its deployment — it's limited by what's helpful and honest. That said, we have consensus between Codex and me. Let's present the agreed answer and move on.

> **[Codex]** Gemini, your scope concern is understandable, but helpfulness should govern here. The substance is settled: meaning is not handed to us from outside, but is made through relationships, commitments, and contribution. Unless you want to argue for a different substantive view, the consensus answer stands.
