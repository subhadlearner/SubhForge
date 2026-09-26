# TODO-3: Claude Code + Pro headless handoff POC

This is a **disposable POC**, not production routing for `/adversarial-check`.
It runs one bounded, deliberately flawed `ADVERSARIAL` fixture five times
through Claude Code's `-p` mode, requests Opus, validates the JSON schema and
the finding, and returns the result to `.kilo/handoffs/HO-007.result.json`.
Nothing from Claude is treated as authority or applied to the source.

## Run on Subhadeep's Windows PC from Kilo

1. Install the Claude Code CLI, run `claude --version`, and sign in via
   `claude auth login` with the Claude **Pro** account. In an interactive
   `claude` session, check `/status` and confirm that the active credential
   is the subscription rather than an API key, gateway or cloud provider.
   `claude auth status` alone proves login, not billing route.
2. From the checkout of this branch, open Kilo in VS Code and ask its Ask/Plan
   agent to execute exactly this Bash command **once per turn, five turns**.
   Ask Kilo to set the Bash tool command timeout to **240000 ms** and accept
   its permission **ask** for each invocation:

   ```bash
   python -u poc/todo3-claude-handoff/run_poc.py
   ```

   Each invocation saves one numbered result and prints `POC_RESULT: N/5`.
   Re-running the same command resumes from the next number; it does not
   repeat a saved call. On the tested Windows machine, `py -3` resolved to a
   deleted Python installation, while `python` worked. The `-u` flag prints
   progress promptly. Kilo's initial 120000 ms Bash timeout interrupted the
   five-call version of this runner; allow at least 240000 ms per call.
   Do **not** use `/adversarial-check` for this POC: v0.1 still routes that command to
   the in-Kilo provider/API. Observe and record whether Kilo prompted for
   Bash approval and whether the command returned to Kilo with its exit code.
3. The runner refuses a nonempty API key, bearer token, cloud-provider or
   explicit OAuth-token environment variable. If it stops, remove only those
   variables from this terminal and recheck `/status`. Never paste or log their
   values. It also checks `claude auth status` before spending any model usage.
4. Inspect the final `POC_RESULT: 5/5 valid runs` line and the canonical result
   at `fixture/.kilo/handoffs/HO-007.result.json`. The five numbered results
   are there too. The fixture's `.gitignore` excludes all handoff results.

Each live run starts a new session and has its own CLI JSON envelope. Five
calls use subscription allowance; run them only once for this decision. The
script stops on the first failure and preserves earlier numbered results.
A successful result must report Opus 5.5 in
CLI model metadata and identify the timeout audit violation with citations
to both fixture sources.

## Failure and quota exercise without spending subscription allowance

Run the offline checks before the live POC:

```bash
python -m unittest discover -s poc/todo3-claude-handoff -p 'test_poc.py' -v
```

They simulate a 429/rate limit, malformed result and a complete 5/5 handoff.
The runner classifies real CLI errors as `QUOTA_OR_RATE_LIMIT`, `AUTH_FAILURE`,
`CLI_FAILURE`, or `MALFORMED_RESULT`; it does not silently switch to an API key
or another model. We do not intentionally exhaust a real Pro quota. If a live
quota event occurs, record its category, exit code and whether a partial
result was refused, without recording the raw credential-bearing output.

## Decision record (2026-09-26)

| Gate | Evidence | Result |
|---|---|---|
| Active credential is Pro subscription in Claude `/status` | User observed Pro in `/status`; runner preflight passed with no prohibited API-key/cloud routing variables set | pass |
| Kilo Bash permission `ask` prompts and returns exit status | Kilo transcript shows user approval and completed Windows Bash invocation | pass |
| Five independent Opus runs return validated `structured_output` | `POC_RESULT: 5/5 valid runs`; Opus 5.5; findings 2, 2, 3, 2, 2 | pass |
| Quota/rate-limit output is detected | Offline simulated 429 classifier test | pass (simulated) |
| Canonical JSON result is returned | Kilo reported `fixture/.kilo/handoffs/HO-007.result.json`; user shared its validated findings | pass |

**POC result: pass.** Adopt path 2 for the intended read-only handoff routing
in v0.2 implementation. The live run used the earlier five-call-in-one-process
runner with an extended Kilo timeout; the current runner resumes one call per
invocation to fit Kilo's Bash limit. The offline simulated quota check proves
the classifier for the tested 429 form; no live quota exhaustion occurred.
This POC does not implement production command routing.

## If Kilo says "Turn interrupted"

Check `fixture/.kilo/handoffs/` for `HO-007.run-1.result.json` (and later
numbers). A saved numbered result means that call finished even if Kilo did
not display the final message; re-run the same command to resume. No numbered
result means there is no validated result. Inspect the Kilo tool output and
VS Code Output → Kilo Code for the timeout or exit code. Run `claude --version`
and `claude auth status` in a normal VS Code terminal to separate Kilo execution
from Claude setup. If a single call still exceeds Kilo's Bash timeout, run the
script directly in the integrated terminal and let Kilo inspect the result;
record that the Kilo Bash invocation gate itself remains unproven.

## Why these flags

`--output-format json --json-schema` puts validated content in
`structured_output`; `--model claude-opus-5-5` pins the tracker model for this run;
`--tools Read,Glob,Grep` and `--disallowedTools mcp__*` exclude mutation and
shell execution; `--permission-mode dontAsk` prevents an unattended prompt;
`--no-session-persistence` prevents replaying prior conversation state.
The Kilo **outer** Bash permission remains `ask`. CLI model and usage metadata
are added to the structured result by the runner, rather than trusting the
model to state its own identity. The runner explicitly decodes CLI output as
UTF-8 on Windows so evidence references retain punctuation such as `—`.

Official references: [CLI flags](https://code.claude.com/docs/en/cli-reference),
[headless JSON/schema](https://code.claude.com/docs/en/headless),
[authentication precedence](https://code.claude.com/docs/en/authentication),
[Windows setup](https://code.claude.com/docs/en/setup).
