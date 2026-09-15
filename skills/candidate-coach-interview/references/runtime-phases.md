# Reasoning level at phase boundaries

Checked 15 September 2026 against official OpenAI documentation and the available Codex desktop tool schemas at that time; check the current runtime before relying on a control. Desired policy: current model with `low` reasoning while recording the block; restore the pre-interview analysis effort for source checks, assessment and recommendations. Do not pick a cheaper/different model unasked.

## What can actually be controlled

The documented Codex App Server allows `effort` overrides on `turn/start`; they become defaults for later turns. That is a client-side configuration operation for a new turn, not an instruction a skill can issue to the model currently generating. [Official App Server documentation](https://learn.chatgpt.com/docs/app-server)

Some Codex desktop runtimes expose `mcp__codex_app__send_message_to_thread` with `thinking:"low"` for a follow-up to an existing Codex task (omit `model` to keep it). It sends a visible new prompt and starts/continues task work; it is not a standalone settings toggle. `create_thread` also accepts thinking but must not be used without an explicit request for a new task. That tool does not set reasoning effort for the active Voice session or silently changes the current generating turn. A Codex-task override does not establish that a separate realtime voice model changed its effort.

## Supported workflow

- Before capture, when a caller is already authorised to dispatch a follow-up to the designated existing interview task, it can pass `thinking:"low"` with the capture prompt. The prompt should say to use/resume the saved block, capture only and stop at `phase:"review"`. This is a real task-turn override only after the tool accepts it. Do not send messages to yourself as a hidden workaround or dispatch new tasks.
- At block end, a caller can dispatch the analysis follow-up to that same existing task with the previous suitable thinking level explicitly restored. Omitting `thinking` would retain low. Keep model unchanged. If the previous level is unknown, do not claim restoration; use the user's chosen analysis setting.
- Without such a caller, the smallest fallback is two turns in the same task: the candidate sets a supported low effort before starting capture, then restores their normal analysis effort and asks to evaluate the stored session. The CLI documents `/model` for model/effort selection and `/status` for checking the setting. This documents a CLI option, not proof of an identical Voice control. Use the actual available app control if present, without claiming it controls an active voice session. [Official developer commands](https://learn.chatgpt.com/docs/developer-commands?surface=cli)
- If the active Voice runtime offers no verified phase switch, say so once before training. Still use the efficient capture-only helper; report a low-effort preference as **not runtime-verified**. At block end, retain all answers and offer evaluation in a subsequent task turn with the desired setting. Do not quietly perform low-effort analysis, automatically end voice, create another task or delegate the interactive interview to subagents.

## Truthful reporting

The Python helper performs deterministic storage/selection with no model calls. It cannot enforce reasoning settings. Its `phase` output and this skill's prose describe workflow state, never observed model configuration. Report “low applied to the Codex follow-up” only after a successful supported configuration call; distinguish it from unverified Voice effort. Installing this skill does not apply a configuration override. Sandbox, tool and model latency can remain; there is no response-time guarantee.
