# N3MemoryCore for Antigravity (N3MC-Free-Antigravity)

**Give Antigravity a memory that does not fade.**

Antigravity forgets what you were working on when a conversation ends.
N3MemoryCore saves every user message and assistant reply in a local SQLite file on your PC, and brings related historical context back whenever relevant topics arise. You do not have to say "remember this", and Antigravity does not need to call a search tool: background hooks handle both saving and context injection automatically.

```bash
git clone https://github.com/NeuralNexusNote/n3mc-free-antigravity.git
cd n3mc-free-antigravity
pip install -e .
n3mc-free-antigravity --init
```

Then restart Antigravity. Memory works from the next session.

> A NeuralNexusNote™ product
>
> 🇯🇵 **[日本語ドキュメント (README_JP.md)](./README_JP.md)**
> 🛡️ **[開発哲学と設計方針 (PHILOSOPHY.md)](./PHILOSOPHY.md)**

---

## Key Characteristics & Differences from Main Free

1. **Coexistence with Main Free (`n3memorycore-free`)**:
   - This package (`n3memorycore-free-antigravity`) is completely decoupled from the main Claude Code edition (`n3memorycore-free`). Both can be installed in the same Python environment without collision.
   - Distinct package name (`n3memorycore_free_antigravity`), CLI command (`n3mc-free-antigravity`), data directory (`~/.n3mc-free-antigravity`), and default resident server port (`18527`).
2. **Standalone by Default, Shareable via Server Connection (§3.7)**:
   - By default, operates independently with its own local database (`~/.n3mc-free-antigravity/.memory/n3memory.db`) and server on port 18527.
   - To share memories with Claude Code / Codex, configure `config.json` with `"connect_server_port": 18520` and `"connect_server_root": "<path to ~/.n3mc>"`. In this mode, saves and searches forward to the connected server. If the partner server is offline, searches return "memory search unavailable" and saves are logged safely in `audit.log`.
3. **Upgrading from Earlier Antigravity Editions**:
   - Re-installation is required: run `pip install -e .` and `n3mc-free-antigravity --init`.
   - `--init` automatically replaces legacy `n3memorycore` hook entries in `~/.gemini/config/hooks.json`.
   - Past records saved in `~/.n3mc` remain safely preserved.

## Hook System

Configured automatically via `~/.gemini/config/hooks.json`:
- **PreInvocation (`n3mc-free-antigravity-hook`)**: Injects `# Recalled Memory Context` into system messages and ensures turn uniqueness.
- **Stop (`n3mc-free-antigravity-stop-hook`)**: Records assistant replies and updates `.agents/rules/n3mc-behavior.md`.
