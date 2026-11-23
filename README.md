# N3MemoryCore for Antigravity (N3MC-Free-Antigravity)

**Give Antigravity a memory that does not fade.**

Antigravity forgets what you were working on when you close the conversation.
N3MemoryCore saves every message and reply in a file on your own PC, and brings
the related ones back the next time you talk about the same thing. You do not
have to say "remember this", and Antigravity does not have to call a search
tool: the hooks do both on every turn.

```bash
git clone https://github.com/NeuralNexusNote/n3mc-free-Antigravity.git
cd n3mc-free-Antigravity
pip install -e .
n3mc-free-antigravity --init
```

Then restart Antigravity. Memory works from the next session. The first run
downloads the search model (about 1.1 GB) once. Details: [Setup](#setup).

> **⚠️ How long memories are kept, and data size**
>
> - **Memories are not deleted.** This edition has no feature that deletes old records; they stay after a year without changing any setting.
> - **More data makes it slower.** The more records there are, the longer a search takes.

> A NeuralNexusNote™ product
>
> 🇯🇵 **[Click here for the Japanese Documentation (日本語版)](./README_JP.md)**
> 🛡️ **[Development Philosophy & AI-Native Policy](./PHILOSOPHY.md)**

## How It Works

```
User's message
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. Auto-save │────▶│ 2. Semantic   │────▶│ 3. Context    │
│  Save message │     │    search     │     │    injection   │
│  and reply    │     │  Find related │     │  Feed to       │
│  to DB        │     │  memories     │     │  Antigravity   │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          Antigravity responds
                                          with full context
```

Powered by Antigravity's hook system (`PreInvocation` and `Stop`). Everything happens automatically — no user action required.

- **What is saved** — every message you send and every reply of Antigravity, as written. A fenced code block is saved as `[code omitted]`: N3MC remembers what was said and decided, and the code is in your project's files.
- **What is recalled** — with every message, the hook searches the memory and adds the related records to Antigravity's context, before Antigravity reads your message.

### Three scenes

> **Monday** — You and Antigravity decide to use PostgreSQL for the website, and say why.
>
> **Wednesday** — In a new conversation you ask which database you chose. Monday's decision and its reason arrive in Antigravity's context together with your question. You do not explain it again.
>
> **Friday** — You are working in another folder. When the subject comes up, Monday's decision is recalled there too: this edition keeps one memory for all your project folders.

### What Antigravity receives

This is the block the hook added for the Wednesday question. It was captured from a real run of the hooks (a temporary data folder; the second conversation was started in a different folder from the first).

```text
# Recalled Memory Context
Search query: Which database did we decide to use for the website, and why?

## Top matches (use these to answer the question)

_If several versions of the same content appear, the one with the newest `saved` time is the current one._

## [1] score=0.5283 saved=2026-11-23 16:32 (UTC+0900) antigravity
[user] Let's use PostgreSQL for the website's database. Several people will edit at the same time, and SQLite locks the whole file on every write.

## Possibly related (weak matches — may be unrelated)

## [2] score=0.3340 saved=2026-11-23 16:32 (UTC+0900) antigravity
[assistant] Agreed, PostgreSQL it is. The reason, for the record: several editors at the same time, and SQLite allows one writer at a time. Next step: write the schema for the articles table.

## Previous matching Q-A exchanges (supplementary context)

### turn_id: b2a9a033-af73-4cc3-b910-ae8c1a025df5 saved=2026-11-23 16:32 (UTC+0900)
[user] Let's use PostgreSQL for the website's database. Several people will edit at the same time, and SQLite locks the whole file on every write.
[assistant] Agreed, PostgreSQL it is. The reason, for the record: several editors at the same time, and SQLite allows one writer at a time. Next step: write the schema for the articles table.
```

`Top matches` are the records that passed the relevance floors. `Possibly related` are the closest of the records that did not (see [Weak matches](#weak-matches-min_results)). The last part shows the whole exchange a top match belongs to.

## About this project

🛡️ AI-Native Development Policy
This project prioritizes Instructions over Static Code. Please read our [Development Philosophy](./PHILOSOPHY.md) to understand why you should let AI generate your execution environment.

This edition was made by rewriting the specification of [N3MC Free](https://github.com/NeuralNexusNote/n3mc-free) v1.9.1 (for Claude Code) for Antigravity, and generating the code from that specification. Saving and searching work as in the main Free; what differs is how the hooks are wired and the names.

**Two install paths are supported**: install this repository's code with `pip install -e .` and run `n3mc-free-antigravity --init`, or drop the specification into Antigravity and let it build the system. Either way, no manual hook editing. (See [Setup](#setup) below.)

## How this edition relates to the main Free

N3MC Free has one edition per application. **For Antigravity, use this one.**

| | **This edition** | **[N3MC Free](https://github.com/NeuralNexusNote/n3mc-free)** (main) |
|---|---|---|
| Works with | Antigravity | Claude Code |
| Package | `n3memorycore-free-antigravity` | `n3memorycore-free` |
| Command | `n3mc-free-antigravity` | `n3mc` |
| Data folder | `~/.n3mc-free-antigravity` | `~/.n3mc` |
| Server port (default) | `18527` | `18520` |
| Where the hooks are registered | `~/.gemini/config/hooks.json` | `~/.claude/settings.json` |
| Rules file | `.agents/rules/n3mc-behavior.md` | `.claude/rules/n3mc-behavior.md` |
| Variable that moves the data | `N3MC_FREE_ANTIGRAVITY_HOME` | `N3MC_HOME` |

- **Both can be installed on one PC.** The names, the data folders and the ports all differ, so they do not collide.
- **As installed, the memories are separate.** This edition saves to its own database (`~/.n3mc-free-antigravity/.memory/n3memory.db`) and does not see the main Free's records.

### Sharing one memory with Claude Code (connection mode)

Connect this edition to the main Free's resident server, and Antigravity and Claude Code use one database. Add these two settings to `~/.n3mc-free-antigravity/config.json`:

```json
"connect_server_port": 18520,
"connect_server_root": "C:/Users/<your user name>/.n3mc"
```

`connect_server_root` is the absolute path of the other side's data folder. This edition connects only when it matches the data folder the other server reports.

- **While connected** — saves and searches go to the other server. This edition's own database is not used. Antigravity's records carry `antigravity` as the agent that wrote them.
- **When the other server is not running** — this edition does not start it. A search shows "memory search unavailable", and your messages do not reach the database: they are kept only in `audit.log`. A `⚠️ N3MC notice` line in the recalled block tells you so.
- **Earlier records** — records saved in this edition's own database before you connected are not moved to the other database. This edition has no command that moves records.
- **Commands** — `--list`, `--show-turn` and `--recall-thread` read the other database read-only. Run `--repair` on the other side.

Remove the two settings to go back to standalone.

### If you used an earlier Antigravity edition

The earlier Antigravity edition used the same names as the main Free (Python package `n3memorycore`, command `n3mc`, data folder `~/.n3mc`). This edition has its own names, so it has to be installed again.

- Run `pip install -e .`, then `n3mc-free-antigravity --init`.
- `--init` replaces the old entry (`n3memorycore`) in `~/.gemini/config/hooks.json` with the new one. If the old entry holds other commands, it is kept, and `--init` prints a line about it.
- Earlier records in `~/.n3mc` stay where they are. This edition sees them only in [connection mode](#sharing-one-memory-with-claude-code-connection-mode).

**This edition is not the right tool if:**

- you use an application other than Antigravity — for Claude Code, use the main [N3MC Free](https://github.com/NeuralNexusNote/n3mc-free);
- you want old records removed for you, or want to delete single records — this edition has no delete command;
- you want the same memory on two PCs — this edition keeps one file on one PC and does not synchronize it.

---

## Features

| You want to… | N3MemoryCore… | How |
|---|---|---|
| Stop explaining the same thing again | saves every message and reply, and recalls the related ones on every turn | Antigravity hooks (`PreInvocation`, `Stop`). No tool call, no manual step |
| Find things in your own words | finds a past conversation even when the exact words differ | Vector search with `intfloat/multilingual-e5-base` (Japanese, English, Chinese, Korean and ~100 other languages) plus keyword search |
| Pick up tomorrow where you left off | keeps the memory across conversations and across project folders | One database for every folder; the conversation you are in is ranked first |
| Keep your data at home | stores the memory in a file on your own PC, not in any cloud service | SQLite. Only the memories recalled for a turn are sent to the model, together with your message ([details](#your-memory-stays-on-your-pc)) |
| Keep the injected context short | does the search with local embeddings and injects only the related records | The recalled block is capped (`top_matches_max`, `min_results`) |
| Share one memory with Claude Code | connects to the main Free's resident server and keeps who wrote each record | [Connection mode](#sharing-one-memory-with-claude-code-connection-mode). `agent_name` is `antigravity` |

To use another embedding model, set it in `config.json` and run `n3mc-free-antigravity --reembed`; the model must produce 768-dimension vectors.

## Your Memory Stays on Your PC

An AI that remembers you is convenient, but it is natural to ask where those memories are kept. N3MemoryCore keeps them in one place you control: a folder on your own PC.

- **One local file** — Every memory is stored in a single SQLite file, `~/.n3mc-free-antigravity/.memory/n3memory.db`. There is no N3MC account and no N3MC cloud service. To move it, set `N3MC_FREE_ANTIGRAVITY_HOME` (see [Optional: change where data lives](#optional-change-where-data-lives)).
- **The raw input is kept next to it** — `~/.n3mc-free-antigravity/.memory/audit.log` holds the input of every hook call. It is rotated at 50 MB, and `n3mc-free-antigravity --list` does not show it. Treat it as private data, like the database.
- **Search runs on your PC** — The embedding model and the search run locally. N3MC's server listens only on `127.0.0.1` and rejects requests for any other host name, so other machines on your network cannot reach it.
- **No telemetry** — N3MC sends no usage data anywhere. The code is open, so you can check this yourself.
- **You can see and remove everything** — `n3mc-free-antigravity --list` shows what is stored. Deleting `~/.n3mc-free-antigravity/` removes all of it (see [Uninstall](#uninstall)). Backing up is copying two files (see [Backup and restore](#backup-and-restore)).

What does go over the network:

- **The embedding model download** — On the first search, `intfloat/multilingual-e5-base` (about 1.1 GB) is downloaded from Hugging Face. After that, the Hugging Face library may still check for model updates when the model loads; set `HF_HUB_OFFLINE=1` to stop this once the model is downloaded.
- **What the model reads** — The memories recalled for a turn are added to that turn's context, so they are sent to the provider of the model Antigravity uses, together with your message, as everything you type into Antigravity is. N3MC does not upload your memory database anywhere, but the parts the model uses in a turn are part of that conversation.

## Specification Files

| File | Description |
|---|---|
| `N3MemoryCore_v1.9.1_Free_JP.md` | Free edition, rewritten for Antigravity (Japanese) |
| `N3MemoryCore_v1.9.1_Free_EN.md` | Free edition, rewritten for Antigravity (English) |

The file names are the same as the main Free's specification files; the content is for Antigravity.

## Setup

There are two supported setup paths. (The names are the same as in the specification: Path A is `pip`, Path B is AI-native.)

### Path A — Install with `pip`

#### 1. Install

This edition is not on PyPI. Get the repository and install from it:

```bash
git clone https://github.com/NeuralNexusNote/n3mc-free-Antigravity.git
cd n3mc-free-Antigravity
pip install -e .          # editable install
```

With the editable install, the hooks run the code from that folder: deleting or moving it later stops the memory.

Requirements: Python 3.10+. The first server start will download the embedding model (`intfloat/multilingual-e5-base`, about 1.1 GB) — expect a one-time delay of several minutes, depending on your connection.

#### 2. Connect to Antigravity

```bash
n3mc-free-antigravity --init
```

This command does what is needed to wire N3MC into Antigravity:

- Creates `~/.n3mc-free-antigravity/` (data lives here — DB, config, audit log, PID file).
- Writes `~/.n3mc-free-antigravity/config.json` with auto-generated `owner_id` / `local_id`.
- Registers the `PreInvocation` and `Stop` hooks in `~/.gemini/config/hooks.json` under the name `n3memorycore-free-antigravity`, pointing to the installed `n3mc-free-antigravity-hook` / `n3mc-free-antigravity-stop-hook`, each with a 120-second time limit. This file is a per-user setting, so the hooks fire in Antigravity opened on any folder.
- Leaves hooks of other programs alone.
- Backs up `hooks.json` (`hooks.json.bak-n3mc-<date-time>`) before changing it. If the file is not valid JSON, it changes nothing and tells you.
- Writes the rules file `.agents/rules/n3mc-behavior.md` into the folder where you ran the command (not when that folder is your home folder).

The command is idempotent: re-running it is safe and won't create duplicates.

#### 3. Verify the hook registration

Run this one-liner — it should print `OK`:

```bash
python -c "import json,os; d=json.load(open(os.path.expanduser('~/.gemini/config/hooks.json'), encoding='utf-8')); e=d.get('n3memorycore-free-antigravity',{}); assert any('n3mc-free-antigravity-hook' in c.get('command','').lower() or 'n3memorycore_free_antigravity.n3mc_hook' in c.get('command','').lower() for c in e.get('PreInvocation',[])), 'PreInvocation hook missing'; assert any('n3mc-free-antigravity-stop-hook' in c.get('command','').lower() or 'n3memorycore_free_antigravity.n3mc_stop_hook' in c.get('command','').lower() for c in e.get('Stop',[])), 'Stop hook missing'; print('OK')"
```

If you see an `AssertionError`, re-run `n3mc-free-antigravity --init`.

#### 4. Restart Antigravity

Quit Antigravity completely and start it again. An Antigravity that was open before `n3mc-free-antigravity --init` does not pick up the new hooks.

#### 5. Confirm it's working

In a new conversation, send any message. After Antigravity responds, run:

```bash
n3mc-free-antigravity --list
```

You should see at least two records — one that starts with `[user]` (your message) and one that starts with `[assistant]` (Antigravity's response). If the list is empty, jump to **Troubleshooting** below.

#### Optional: change where data lives

Set `N3MC_FREE_ANTIGRAVITY_HOME=/path/to/dir` to keep the data somewhere else. N3MC reads the variable every time it runs and does not store it, so set it **permanently**, where both Antigravity (which starts the hooks) and your terminal see it — for example as a user environment variable — before running `n3mc-free-antigravity --init`. If it is set only in the terminal where you ran `--init`, the hooks use `~/.n3mc-free-antigravity`.

---

### Path B — AI-Native Setup

Let Antigravity generate the code from the specification:

1. Create an **empty folder** (for example `~/n3mc-free-antigravity`) and put one specification file from the table above into it
2. Open Antigravity in that folder
3. Say: "Please implement N3MemoryCore according to this specification."

Antigravity shows the folder and asks you once to confirm it; then it writes the code, configures the hooks, and sets everything up. It stops instead if the folder holds other files, so that a project of yours is not overwritten.
Memory kicks in from the next session. The generated code stays in that folder: deleting or moving it later stops the memory.

---

### Troubleshooting (Path A)

**`n3mc-free-antigravity: command not found` after `pip install`**
Your Python `Scripts/` (Windows) or `bin/` (Linux) directory is not on `PATH`. Either add it to `PATH`, or invoke as `python -m n3memorycore_free_antigravity.n3memory --init` instead.

**`--list` shows zero records after a real conversation**
Antigravity was open **before** you ran `n3mc-free-antigravity --init`. Quit it completely and start it again.

**Hooks register, but nothing saves**
Check the audit log:
```bash
cat ~/.n3mc-free-antigravity/.memory/audit.log | tail -3
```
Each message should add JSON lines. If the file is empty, the hooks aren't firing — confirm Step 3's verification command prints `OK`.

**`n3mc-free-antigravity --search` returns nothing the first time, but works after**
The `intfloat/multilingual-e5-base` model is downloading (about 1.1 GB) on the first call. Wait for the download to finish, then retry.

**The recalled block says "memory search unavailable"**
You are in [connection mode](#sharing-one-memory-with-claude-code-connection-mode) and the other server is not running. Start Claude Code and send a message: that starts the main Free's server.

### What to expect after setup

Once setup is complete, everything works automatically from the next session:
- Past conversations relevant to your current message are retrieved and injected automatically
- Antigravity responds with full context ("Regarding what we discussed last time...")
- Saving and searching happen in the background — no action needed on your part
- The Stop hook writes a small rules file, `.agents/rules/n3mc-behavior.md`, into each project folder you work in. It tells Antigravity how to read the recalled block; a file you edited by hand is not replaced

### Tuning recall (vector_min_cos)

N3MC finds records whose meaning is close to your question with vector search.
`vector_min_cos` is the threshold for "how close is close enough to be a
candidate" (default 0.82; the specification's value is 0.85).

| If you | What happens |
|---|---|
| lower it (e.g. 0.80–0.83) | Records are found even when the wording differs, and short questions recall more. Less related records also come in, and the injected context gets longer |
| raise it (e.g. 0.88) | Fewer loosely related records and shorter injected context. Related records are also dropped more easily |

A sensible range is 0.80–0.88. Set it in `~/.n3mc-free-antigravity/config.json`,
e.g. `"vector_min_cos": 0.83`. It takes effect from the next question (the
server restarts automatically). If the file has a typo and cannot be read, it is
left untouched and N3MC runs with defaults until you fix it; a notice about this
appears at the top of the recalled context. Write numbers without quotes.

### Search settings on by default

Four more settings keep unrelated records out of the recalled context. They are
the same as in the main Free and are on by default. They run on the CPU and
need no other model.

| Setting | Default | What it does | To turn it off |
|---|---|---|---|
| `fts_stopwords` | `true` | English function words (`the`, `is`, `of`, `who`, ...) are not used as keywords, so a question made of common words no longer matches almost every record | `false` |
| `kw_only_min_terms` | `3` | A record found by its keywords only (not close enough in meaning) goes under Top matches only when it contains 3 different words of the question. Otherwise it can still appear as a weak match | `0` |
| `top_matches_max` | `5` | At most 5 records under Top matches, so the recalled context stays short | `0` (then up to `search_result_limit`) |
| `cross_lang_min_cos` | `0.80` | A Japanese question can find an English record and the other way round: the closest record written in the other script counts as a match from this similarity on | `0` |

These settings are not in the specification (`N3MemoryCore_v1.9.1_Free_*.md`),
so code generated again from it does not have them. For the specification's
search exactly, write `"vector_min_cos": 0.85, "fts_stopwords": false,
"kw_only_min_terms": 0, "top_matches_max": 0, "cross_lang_min_cos": 0` in
`~/.n3mc-free-antigravity/config.json`.

### Weak matches (min_results)

When fewer than 3 records pass the relevance floors, N3MC adds the closest
of the records it dropped, up to 3 in total, under a separate heading
`## Possibly related (weak matches — may be unrelated)`. Antigravity is told to
use them only when they are actually relevant. This keeps a question from
getting no memory at all, at the cost of up to 3 extra, mostly unrelated chunks
per turn. Set `"min_results": 0` in `~/.n3mc-free-antigravity/config.json` to
turn it off, or another number to change the count.

Old records are never hidden by their age: age only lowers their rank below
newer records of the same relevance.

### Backup and restore

To migrate memories to another environment or keep a safe backup, save these 2 files
from `~/.n3mc-free-antigravity/`:
- `.memory/n3memory.db` — the memory database
- `config.json` — contains `owner_id` and `local_id` UUIDv4 keys

Keep these 2 files together: `config.json` holds the IDs that are stamped on the records in the database.

### Uninstall

If you set up via Path B, ask Antigravity: "Please delete N3MemoryCore." — it also removes the hook configuration.

To do it yourself:

1. Remove the `n3memorycore-free-antigravity` entry from `~/.gemini/config/hooks.json`, and restart Antigravity.
2. Stop the memory server, which keeps running in the background: end the process whose command line contains `n3memorycore_free_antigravity.n3memory --run-server` (its PID is in `~/.n3mc-free-antigravity/.memory/n3mc.pid`), or restart the PC.
3. Remove the package and the data:

```bash
pip uninstall n3memorycore-free-antigravity
rm -rf ~/.n3mc-free-antigravity/                     # delete data (irreversible)
```

4. `.agents/rules/n3mc-behavior.md` in your project folders, and the `hooks.json.bak-n3mc-*` backups next to `hooks.json`, can be deleted by hand.

## ID Hierarchy

N3MemoryCore uses 6 ID fields to identify the origin and context of each record:

| ID | Stored in | Generated | Granularity | Purpose |
|---|---|---|---|---|
| `id` (PK) | DB record | Per record (UUIDv7, time-ordered) | **One record** | Unique identifier for each memory |
| `owner_id` | `config.json` | First startup (UUIDv4) | **Owner / data folder** | Identifies whose data this is |
| `local_id` | `config.json` / API | First startup (UUIDv4), or per request | **Install** | One install has one `local_id`; it is the same in every session. Stored on every record (in Free it is not used in ranking) |
| `session_id` | Supplied by Antigravity (`conversationId` in the hook input) | Per conversation | **One conversation** | Groups the memories of one conversation. Drives the `b_session` ranking bias (match=1.0, mismatch=0.6) so the ongoing exchange ranks above unrelated past conversations |
| `turn_id` | DB record | When your message is saved (UUIDv4) | **One exchange** | Ties one user message to the reply that answers it; `--show-turn` and `--recall-thread` take it |
| `agent_name` | DB record | Per save (free-form string) | **Display label** | Human-readable label of the writer (`"antigravity"` for the hooks). `--buffer --agent-id <name>` sets this field |

```
owner_id  (the data folder ~/.n3mc-free-antigravity and its owner)
  └── local_id  (the install; the same in every session)
        └── session_id  (one Antigravity conversation)
              └── turn_id  (one exchange: one user message and the reply to it)
                    └── id  (one record = one chunk)

agent_name  (a display label, outside the hierarchy: "antigravity" for the hooks)
```

## Requirements

- **Antigravity** (required; its hook system is used)
- **Python 3.10+**
- **OS**: Windows 11 and Linux. macOS is not supported.

> To check if Python is installed, run `python --version` in your terminal.

## Extensibility

N3MemoryCore is built from a specification, so extending it is as simple as asking Antigravity: load the specification into Antigravity and say what you want to add. When you customize it, tell Antigravity where the specification is and ask it to update the specification too.

## ⚠️ Disclaimer

- **No support, no claims**: This project is provided as-is with no support. Questions, bug reports, and feature requests are not guaranteed a response. Use entirely at your own discretion.
- **Use at your own risk**: This system runs on AI-generated code. The author is not responsible for any data changes or issues caused by its use.
- **Backup first**: Always back up your current environment before running this on important projects.

---

Apache License 2.0 — Copyright (C) 2026 NeuralNexusNote™ / ArnolfJp019
See [LICENSE](./LICENSE) for details.
