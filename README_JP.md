# N3MemoryCore for Antigravity (N3MC-Free-Antigravity)

**Antigravity に色褪せない記憶を。**

Antigravity は会話を終了すると作業内容を忘れてしまいます。
N3MemoryCore はすべてのメッセージと応答をお手元の PC の SQLite データベースに保存し、次回関連する話題が出た際に自動でコンテキストを引き出します。「これを覚えておいて」と指示する必要も、検索ツールを手動で呼ぶ必要もありません。バックグラウンドフックが自動で保存と想起を行います。

```bash
git clone https://github.com/NeuralNexusNote/n3mc-free-antigravity.git
cd n3mc-free-antigravity
pip install -e .
n3mc-free-antigravity --init
```

その後、**Antigravity を再起動**してください。次のセッションから記憶が有効になります。

> A NeuralNexusNote™ product
>
> 🇬🇧 **[English Documentation (README.md)](./README.md)**
> 🛡️ **[開発哲学と設計方針 (PHILOSOPHY.md)](./PHILOSOPHY.md)**

---

## 本体の Free 版との違い・同居について

1. **本体の Free（`n3memorycore-free`、Claude Code 用）との同居**:
   - 本パッケージ（`n3memorycore-free-antigravity`）は、本体の Claude Code 用 Free 版と完全に分離されています。同一 PC・同一 Python 環境に同時にインストールしても衝突しません。
   - パッケージ名（`n3memorycore_free_antigravity`）、CLI コマンド（`n3mc-free-antigravity`）、データフォルダ（`~/.n3mc-free-antigravity`）、既定ポート（`18527`）がそれぞれ独立しています。
2. **通常は単独動作、設定で本体サーバーと記憶を共有可能（§3.7）**:
   - 既定では単独で動作し、専用の DB（`~/.n3mc-free-antigravity/.memory/n3memory.db`）とポート 18527 のサーバーを使用します。
   - Claude Code や Codex と同じ記憶を共有したい場合は、`config.json` に `"connect_server_port": 18520` と `"connect_server_root": "<~/.n3mc の絶対パス>"` を設定します。接続モードでは保存・検索が本体サーバーにフォワードされます。本体サーバーが動いていない場合、検索は「memory search unavailable」となり、発言は `audit.log` のみに安全に記録されます。
3. **以前の Antigravity 版をお使いだった方へ**:
   - コマンド名やパッケージ名が新しくなったため、`pip install -e .` による入れ直しと `n3mc-free-antigravity --init` の実行が必要です。
   - `--init` は `~/.gemini/config/hooks.json` 内の古い `n3memorycore` 登録を自動で新しい登録へと置き換えます。
   - 以前 `~/.n3mc` に保存された記録はそのまま残ります。

## フックの仕組み

`~/.gemini/config/hooks.json` によって自動実行されます：
- **PreInvocation (`n3mc-free-antigravity-hook`)**: 過去の関連記憶（`# Recalled Memory Context`）をシステムメッセージとして注入し、ターンの重複実行を防止します。
- **Stop (`n3mc-free-antigravity-stop-hook`)**: アシスタントの応答を保存し、ワークスペース内の `.agents/rules/n3mc-behavior.md` を整備します。
