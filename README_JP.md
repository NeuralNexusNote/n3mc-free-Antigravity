# N3MemoryCore Free for Antigravity (n3mc-free-Antigravity) v1.9.1

**Antigravity に、消えない記憶を。無料で、あなたの PC の中に。**

Antigravity は、会話を閉じると、何を話していたかを忘れます。
N3MemoryCore は、発言と返答をすべて、あなたの PC のファイルに保存します。
次に同じ話をしたとき、関係のある記憶を自動で呼び出します。
あなたが「覚えて」と言う必要も、Antigravity が検索のツールを呼ぶ必要もありません。
どちらも、フックが毎ターン行います。
AI の記憶のうち、N3MC は**会話履歴**の層（いつ、どの会話で、何を話したかの記憶）を受け持ちます。いつも読み込むルールファイルなどの決まりや、外部ツールとの連携は受け持ちません。

1. エクスプローラーで、空のフォルダを作る
2. そのフォルダに指示書 `N3MemoryCore_v1.9.1_Free_JP.md` を入れる(指示書のほかに何も入れない)
3. そのフォルダで Antigravity を開く
4. 「この指示書 `N3MemoryCore_v1.9.1_Free_JP.md` に従って N3MemoryCore を実装してください」と送る
5. 終わったら、Antigravity を再起動する（[Antigravity を再起動する](#4-antigravity-を再起動する) を見てください）

次のセッションから記憶が働きます。
最初の 1 回だけ、検索用のモデル（約 1.1 GB）のダウンロードがあります。詳しくは [セットアップ](#セットアップ) を見てください。
PyPI から入れる方法（おまけ）は [方法 B：パッケージ導入（おまけ）](#方法-bパッケージ導入おまけ) にあります。

> **⚠️ ご利用にあたって**
>
> - **ノーサポート・ノークレーム**: 本プロジェクトはサポートを提供していません。動作に関する問い合わせ・不具合報告・機能要望への対応は保証されません。すべて自己責任のもとでご利用ください。
> - **自己責任**: 本システムはAIが生成したコードで動作します。導入によるデータの変化や不具合については、製作者は責任を負いかねます。
> - **バックアップ**: 大切なプロジェクトで実行する前に、必ず現在の環境をバックアップしてください。

> **⚠️ 記憶の保持期間とデータ量**
>
> - **記憶は消えません。** この版には、古い記録を消す機能はありません。
> - **データ量が増えると遅くなります。** 記録が増えるほど、検索に時間がかかるようになります。

> A NeuralNexusNote™ product
>
> 🇺🇸 **[Click here for the English Documentation](./README.md)**
> 🛡️ **[開発理念 & AI-Native Policy](./PHILOSOPHY.md)**

## 仕組み

```
ユーザーの発言
    │
    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. 自動保存  │────▶│  2. 意味検索  │────▶│ 3. コンテキスト│
│  発言と返答を │     │  関連する過去 │     │    注入       │
│  DBに保存    │     │  の記憶を取得 │     │ Antigravityに │
│              │     │              │     │    渡す       │
└──────────────┘     └──────────────┘     └──────────────┘
                                                 │
                                                 ▼
                                          Antigravityが過去の
                                          文脈を踏まえて回答
```

Antigravity のフック機能（`PreInvocation` と `Stop`）を利用し、すべて自動で行われます。ユーザーが意識する必要はありません。

- **保存するもの** — あなたの発言と Antigravity の返答を、すべてそのまま保存します。コードブロック（``` で囲んだ部分）は `[code omitted]` として保存します。N3MC が覚えるのは、話したことと決めたことです。コードは、プロジェクトのファイルにあります。
- **呼び出すもの** — 発言のたびに、フックが記憶を検索します。関係のある記録を、Antigravity があなたの発言を読む前に、コンテキストに加えます。

### 3 つの場面

> **月曜** — Antigravity と相談して、サイトのデータベースを PostgreSQL にすると決めます。理由も話します。
>
> **水曜** — 新しい会話で、「データベースは何にしたか」と聞きます。月曜の決定と理由が、質問と一緒に Antigravity に届きます。説明し直す必要はありません。
>
> **金曜** — 別のフォルダで作業しています。その話題になると、月曜の決定がここでも呼び出されます。この版は、すべてのプロジェクトのフォルダで 1 つの記憶を使います。

### 実際に Antigravity に届くもの

水曜の質問のときに、フックが加えた塊です。フックを実際に動かして取ったものです（一時的なデータフォルダを使い、2 つ目の会話は 1 つ目と別のフォルダで始めました）。

```text
# Recalled Memory Context
Search query: サイトのデータベースは、何にすると決めましたか。理由も教えてください。

## Top matches (use these to answer the question)

_If several versions of the same content appear, the one with the newest `saved` time is the current one._

## [1] score=0.5472 saved=2026-11-23 16:32 (UTC+0900) antigravity
[user] サイトのデータベースは PostgreSQL にしましょう。複数の人が同時に編集する予定で、SQLite は書き込みのたびにファイル全体をロックするからです。

## [2] score=0.4790 saved=2026-11-23 16:32 (UTC+0900) antigravity
[assistant] 承知しました。データベースは PostgreSQL にします。理由は、同時に編集する人がいることと、SQLite は書き込みが 1 つずつになることです。次は、記事のテーブルの定義を書きます。

## Previous matching Q-A exchanges (supplementary context)

### turn_id: 5d593cdd-3e1c-4591-a46d-804af930bb6a saved=2026-11-23 16:32 (UTC+0900)
[user] サイトのデータベースは PostgreSQL にしましょう。複数の人が同時に編集する予定で、SQLite は書き込みのたびにファイル全体をロックするからです。
[assistant] 承知しました。データベースは PostgreSQL にします。理由は、同時に編集する人がいることと、SQLite は書き込みが 1 つずつになることです。次は、記事のテーブルの定義を書きます。
```

`Top matches` は、関連度の下限を通った記録です。下限を通った記録が少ないときは、落ちた記録のうち近いものが `Possibly related` という見出しで加わります（[弱い候補](#弱い候補min_results)）。最後の部分は、上位の記録が入っているやりとりの全体です。

## このプロジェクトについて

🛡️ AI-Native Development Policy
本プロジェクトは静的コードよりも指示書を優先します。AIに実行環境を生成させる理由については [開発理念](./PHILOSOPHY.md) をご覧ください。

この版は、Claude Code 用の [N3MC Free](https://github.com/NeuralNexusNote/n3mc-free) v1.9.1 の指示書を Antigravity 用に書き直し、その指示書から作ったものです。保存と検索の中身は本体の Free と同じで、違うのはフックのつなぎ方と名前です。

**2 つの導入方法**: 指示書を Antigravity に渡して実装させるか（メイン）、パッケージを `pip install n3memorycore-free-antigravity` で入れて `n3mc-free-antigravity --init` を実行するか（おまけ）。どちらの方法でもフック設定は手動編集不要です。（詳細は[セットアップ](#セットアップ)参照）

## 本体の Free との関係

N3MC Free には、使うアプリごとに版があります。**Antigravity で使うなら、この版です。**

| | **この版** | **[N3MC Free](https://github.com/NeuralNexusNote/n3mc-free)**（本体） |
|---|---|---|
| 使うアプリ | Antigravity | Claude Code |
| パッケージ | `n3memorycore-free-antigravity` | `n3memorycore-free` |
| コマンド | `n3mc-free-antigravity` | `n3mc` |
| データフォルダ | `~/.n3mc-free-antigravity` | `~/.n3mc` |
| サーバーのポート（既定） | `18527` | `18520` |
| フックの登録先 | `~/.gemini/config/hooks.json` | `~/.claude/settings.json` |
| ルールファイル | `.agents/rules/n3mc-behavior.md` | `.claude/rules/n3mc-behavior.md` |
| データの場所を変える環境変数 | `N3MC_FREE_ANTIGRAVITY_HOME` | `N3MC_HOME` |

- **同じ PC に両方入れられます。** 名前、データフォルダ、ポートがすべて違うので、ぶつかりません。
- **そのままでは、記憶は別々です。** この版は自分の DB（`~/.n3mc-free-antigravity/.memory/n3memory.db`）に保存し、本体の Free の記録は見ません。

### Claude Code と同じ記憶を使う（接続モード）

本体の Free の常駐サーバーにつなぐと、Antigravity と Claude Code が 1 つの DB を使います。`~/.n3mc-free-antigravity/config.json` に、次の 2 つを書き足します。

```json
"connect_server_port": 18520,
"connect_server_root": "C:/Users/<あなたのユーザー名>/.n3mc"
```

`connect_server_root` は、相手のデータフォルダの絶対パスです。相手のサーバーが答えるデータフォルダと一致したときだけ、つなぎます。

- **つないでいる間** — 保存も検索も、相手のサーバーに送ります。この版の DB は使いません。Antigravity の記録には、書いたエージェントとして `antigravity` が付きます。
- **相手のサーバーが動いていないとき** — この版が相手のサーバーを起動することはありません。検索は「memory search unavailable」と表示され、発言は DB に入らず、`audit.log` にだけ残ります。そのことは、記憶の差し込みの中に `⚠️ N3MC notice` として表示されます。
- **それまでの記録** — つなぐ前にこの版の DB にためた記録は、相手の DB には移りません。この版に、記録を移すコマンドはありません。
- **コマンド** — `--list`・`--show-turn`・`--recall-thread` は、相手の DB を読み取り専用で読みます。`--repair` は、相手の側で実行してください。

2 つの設定を消すと、単独の動きに戻ります。

### 以前の Antigravity 版を使っていた方へ

以前の Antigravity 版は、本体の Free と同じ名前（Python のパッケージ `n3memorycore`、コマンド `n3mc`、データフォルダ `~/.n3mc`）を使っていました。この版は名前が違うので、入れ直しが必要です。

- `pip install n3memorycore-free-antigravity`（またはこのリポジトリで `pip install -e .`）のあと、`n3mc-free-antigravity --init` を実行します。
- `--init` は、`~/.gemini/config/hooks.json` の古い登録（`n3memorycore`）を、新しい登録に置き換えます。古い登録にほかのコマンドが入っているときは、置き換えずに残し、その旨を表示します。
- `~/.n3mc` に保存された以前の記録は、そのまま残ります。この版からは、[接続モード](#claude-code-と同じ記憶を使う接続モード)にしたときだけ見えます。

**次の場合は、この版は向いていません。**

- Antigravity 以外のアプリで使う場合。Claude Code には、本体の [N3MC Free](https://github.com/NeuralNexusNote/n3mc-free) を使ってください。
- 古い記録を自動で消したい場合や、記録を 1 件ずつ消したい場合。この版には、削除のコマンドがありません。
- 2 台の PC で同じ記憶を使いたい場合。この版は、1 台の PC の 1 つのファイルに保存し、同期はしません。

---

## 特徴

| したいこと | N3MemoryCore がすること | 仕組み |
|---|---|---|
| 同じ説明を繰り返したくない | 発言と返答をすべて保存し、関係のあるものを毎ターン呼び出す | Antigravity のフック（`PreInvocation`、`Stop`）。ツールの呼び出しも、手作業も要らない |
| 自分の言葉で探したい | 言い回しが違っても、関係のある過去の会話を見つける | `intfloat/multilingual-e5-base` のベクトル検索（日本語・英語・中国語・韓国語など約 100 言語）と、キーワード検索 |
| 翌日、続きから始めたい | 会話をまたいでも、プロジェクトのフォルダが違っても、記憶が残る | すべてのフォルダで 1 つの DB。今の会話の記録を先に並べる |
| データを手元に置きたい | 記憶を自分の PC のファイルに保存し、クラウドのサービスには置かない | SQLite。モデルに送られるのは、そのターンに呼び出した記憶だけで、メッセージと一緒に送られる（[詳しく](#記憶はあなたの-pc-に残ります)） |
| 差し込みを短く保ちたい | 検索はローカルの埋め込みで行い、関係のある記録だけを差し込む | 差し込む塊には上限がある（`top_matches_max`、`min_results`） |
| Claude Code と 1 つの記憶を使いたい | 本体の Free の常駐サーバーにつなぎ、記録ごとに、書いたエージェントを残す | [接続モード](#claude-code-と同じ記憶を使う接続モード)。`agent_name` は `antigravity` |

ほかの埋め込みモデルを使うときは、`config.json` に書いて `n3mc-free-antigravity --reembed` を実行します。768 次元のベクトルを出すモデルである必要があります。

## 記憶はあなたの PC に残ります

AI が覚えていてくれるのは便利ですが、その記憶がどこに置かれるのかは気になるところです。N3MemoryCore は、記憶をあなたが管理できる 1 か所、つまりあなたの PC の中のフォルダに置きます。

- **ローカルの 1 ファイル** — 記憶はすべて、SQLite のファイル `~/.n3mc-free-antigravity/.memory/n3memory.db` 1 つに保存されます。N3MC のアカウントも、N3MC のクラウドサービスもありません。置き場所は `N3MC_FREE_ANTIGRAVITY_HOME` で変えられます（[オプション: データ位置の変更](#オプション-データ位置の変更)）。
- **入力の原文も、その隣に残る** — `~/.n3mc-free-antigravity/.memory/audit.log` に、フックが受け取った入力が残ります。50 MB で入れ替わります。`n3mc-free-antigravity --list` には出ません。DB と同じく、他人に見せない情報として扱ってください。
- **検索は PC の中で動く** — 埋め込みモデルも検索も、手元で動きます。N3MC のサーバーは `127.0.0.1` だけで待ち受け、ほかのホスト名あての要求は断ります。同じネットワークのほかの機械からは使えません。
- **利用状況を送らない** — N3MC は利用データをどこにも送りません。コードは公開されているので、ご自身で確かめられます。
- **中身を見られる・消せる** — `n3mc-free-antigravity --list` で保存された内容を表示できます。`~/.n3mc-free-antigravity/` を消せば、すべて消えます（[アンインストール](#アンインストール)）。バックアップは 2 つのファイルをコピーするだけです（[バックアップと復元](#バックアップと復元)）。

ネットワークを通るもの:

- **埋め込みモデルのダウンロード** — 最初の検索のときに、`intfloat/multilingual-e5-base`（約 1.1 GB）を Hugging Face から取得します。その後も、モデルを読み込むときに Hugging Face のライブラリが更新を確認することがあります。ダウンロードが済んだ後に `HF_HUB_OFFLINE=1` を設定すると、この確認は止まります。
- **モデルが読む部分** — そのターンに呼び出された記憶はコンテキストに加えられるので、Antigravity に入力した文と同じように、メッセージと一緒に、Antigravity が使うモデルの提供元に送られます。N3MC が記憶の DB をどこかに上げることはありませんが、モデルがそのターンに使う部分は会話の一部になります。

## 指示書一覧

| ファイル | 内容 |
|---|---|
| `N3MemoryCore_v1.9.1_Free_JP.md` | Antigravity 用に書き直した Free 版の指示書（日本語） |
| `N3MemoryCore_v1.9.1_Free_EN.md` | Antigravity 用に書き直した Free 版の指示書（英語） |

ファイル名は本体の Free の指示書と同じですが、中身は Antigravity 用です。

## セットアップ

導入の方法は以下の 2 通りです。指示書から作成する方法 A がメインで、パッケージを入れる方法 B はおまけです。（指示書では、方法 A を「経路 B — AI ネイティブセットアップ」、方法 B を「経路 A — `pip` で導入する」と呼んでいます。）

### 方法 A：指示書から作成（メイン・推奨）

指示書から、Antigravity にコードを生成させます：

1. **フォルダを作る**:エクスプローラーで、空のフォルダを 1 つ作ります(例:`C:\Users\<あなたの名前>\n3mc-free-antigravity`)。コードはこのフォルダに作られ、セットアップのあとも使い続けます。あとで消したり動かしたりしないでください。
2. **指示書を入れる**:上の表の指示書 `N3MemoryCore_v1.9.1_Free_JP.md` を、そのフォルダに入れます(このフォルダには、指示書のほかに何も入れません)。
3. **そのフォルダで Antigravity を開く**
4. **頼む**:「この指示書 `N3MemoryCore_v1.9.1_Free_JP.md` に従って N3MemoryCore を実装してください」と送ります。

Antigravity は、フォルダを表示して 1 回だけ確認を求めます。そのあと、コードの記述、フックの設定、初期設定を行います。フォルダにほかのファイルがあるときは、あなたのプロジェクトを上書きしないように、作業を止めます。
次のセッションから記憶が有効になります。生成したコードは、そのフォルダに残ります。あとでフォルダを消したり動かしたりすると、記憶が止まります。

---

### 方法 B：パッケージ導入（おまけ）

リファレンスビルドをそのまま使います：

#### 1. インストール

最も簡単な方法 — PyPI から直接インストール (clone 不要):

```bash
pip install n3memorycore-free-antigravity
```

ローカルにコードを取得してカスタマイズしたい場合:

```bash
git clone https://github.com/NeuralNexusNote/n3mc-free-Antigravity.git
cd n3mc-free-Antigravity
pip install -e .          # editable install
```

editable install では、フックがそのフォルダのコードを動かします。あとでフォルダを消したり動かしたりすると、記憶が止まります。

要件: Python 3.10+。サーバー初回起動時に埋め込みモデル（`intfloat/multilingual-e5-base`、約 1.1 GB）をダウンロードします。回線によりますが、最初の 1 回だけ数分かかります。

#### 2. Antigravity に接続する

```bash
n3mc-free-antigravity --init
```

このコマンドは、N3MC を Antigravity に接続するために必要な処理を行います:

- `~/.n3mc-free-antigravity/` を作成（DB・設定・監査ログ・PID ファイルがここに集約）
- `~/.n3mc-free-antigravity/config.json` に `owner_id` / `local_id` を自動生成して書き込み
- `~/.gemini/config/hooks.json` に、`n3memorycore-free-antigravity` という名前で `PreInvocation` と `Stop` のフックを登録（インストール済みの `n3mc-free-antigravity-hook` / `n3mc-free-antigravity-stop-hook` を指し、それぞれに 120 秒の制限時間を付ける）。このファイルは利用者ごとの設定なので、どのフォルダで開いた Antigravity でもフックが動く
- ほかのプログラムのフックには触れない
- 変更する前に `hooks.json` のバックアップ（`hooks.json.bak-n3mc-<日時>`）を取る。JSON として読めないファイルは変更せず、その旨を表示する
- コマンドを実行したフォルダに、ルールファイル `.agents/rules/n3mc-behavior.md` を書く（ホームフォルダで実行したときは書かない）

このコマンドは冪等です。再実行しても重複登録されません。

#### 3. フック登録を検証する

以下のワンライナーを実行 — `OK` が出力されれば成功:

```bash
python -c "import json,os; d=json.load(open(os.path.expanduser('~/.gemini/config/hooks.json'), encoding='utf-8')); e=d.get('n3memorycore-free-antigravity',{}); assert any('n3mc-free-antigravity-hook' in c.get('command','').lower() or 'n3memorycore_free_antigravity.n3mc_hook' in c.get('command','').lower() for c in e.get('PreInvocation',[])), 'PreInvocation hook missing'; assert any('n3mc-free-antigravity-stop-hook' in c.get('command','').lower() or 'n3memorycore_free_antigravity.n3mc_stop_hook' in c.get('command','').lower() for c in e.get('Stop',[])), 'Stop hook missing'; print('OK')"
```

`AssertionError` が出る場合は `n3mc-free-antigravity --init` を再実行してください。

#### 4. Antigravity を再起動する

Antigravity を完全に終了して、起動し直してください。`n3mc-free-antigravity --init` の前から開いていた Antigravity には、フックが反映されません。

#### 5. 動作確認

新しい会話で何かメッセージを送信し、Antigravity が応答したあと以下を実行:

```bash
n3mc-free-antigravity --list
```

最低 2 件のレコードが表示されるはずです — `[user]` で始まるもの（あなたのメッセージ）と `[assistant]` で始まるもの（Antigravity の応答）。リストが空の場合は下の **トラブルシューティング** へ。

#### オプション: データ位置の変更

`N3MC_FREE_ANTIGRAVITY_HOME=/path/to/dir` を設定すると、データの保存先を変えられます。N3MC は、動くたびにこの変数を読みます。値をどこかに覚えることはありません。そのため、Antigravity（フックを起動します）とターミナルの両方から見える形で、**恒久的に**設定してください（たとえば、ユーザーの環境変数として）。設定は `n3mc-free-antigravity --init` の前に行います。`--init` を実行したターミナルにだけ設定した場合、フックは `~/.n3mc-free-antigravity` を使います。

---

### トラブルシューティング（方法 B）

**`pip install` 後に `n3mc-free-antigravity: command not found`**
Python の `Scripts/`（Windows）または `bin/`（Linux）ディレクトリが `PATH` に通っていません。`PATH` に追加するか、代替として `python -m n3memorycore_free_antigravity.n3memory --init` を使用してください。

**実際に会話したのに `--list` が 0 件**
`n3mc-free-antigravity --init` を実行する**前から**開いていた Antigravity を使っています。完全に終了して起動し直してください。

**フックは登録されているのに何も保存されない**
監査ログを確認してください:
```bash
cat ~/.n3mc-free-antigravity/.memory/audit.log | tail -3
```
発言ごとに JSON の行が追加されているはずです。空ならフックが発火していません — Step 3 の検証コマンドが `OK` を返すかを確認してください。

**初回 `n3mc-free-antigravity --search` が空を返すが、その後は動く**
`intfloat/multilingual-e5-base` モデル（約 1.1 GB）が初回呼び出し時にダウンロード中です。ダウンロードが終わるのを待ってからリトライしてください。

**記憶の差し込みに「memory search unavailable」と出る**
[接続モード](#claude-code-と同じ記憶を使う接続モード)にしていて、相手のサーバーが動いていません。Claude Code を起動して発言すると、本体の Free のサーバーが起動します。

### セットアップ後の体験

セットアップが完了すると、次のセッションから自動的に動作します：
- あなたの発言に関連する過去の会話が、自動で検索・注入されます
- Antigravity は過去の文脈を踏まえて回答します（「前回話した○○ですが…」）
- 保存も検索もバックグラウンドで行われるため、操作は不要です
- Stop フックが、作業したプロジェクトのフォルダごとに、小さなルールファイル `.agents/rules/n3mc-behavior.md` を書きます。呼び出した塊の読み方を Antigravity に伝えるものです。手で編集したファイルは、置き換えません

### 記憶の呼び出しの調整（vector_min_cos）

N3MC は、質問と意味の近い記録をベクトル検索で探します。`vector_min_cos` は、
「どれくらい近ければ候補にするか」のしきい値です（既定 0.82。指示書の値は 0.85）。

| 値を | 起きること |
|---|---|
| 下げる（例 0.80〜0.83） | 言い回しが違っても拾いやすくなる。短い質問でも記録が出やすい。その分、関係の薄い記録も混ざり、差し込みが長くなる |
| 上げる（例 0.88） | 関係の薄い記録が減り、差し込みが短くなる。その分、関係のある記録も落ちやすい |

目安は 0.80〜0.88 です。値は `~/.n3mc-free-antigravity/config.json` に `"vector_min_cos": 0.83` のように書きます。
保存すると、次の質問から効きます（サーバーは自動で起動し直します）。
書き間違えて読めないときは、ファイルはそのまま残り、直すまで既定値で動きます。そのことは、記憶の差し込みの先頭に表示されます。数値は引用符を付けずに書いてください。

### 既定で有効な検索の設定

関係のない記録を、記憶の差し込みに入れないための設定が 4 つあります。本体の Free と同じもので、どれも既定で有効です。CPU だけで動き、ほかのモデルは要りません。

| 設定 | 既定 | 中身 | 止めるとき |
|---|---|---|---|
| `fts_stopwords` | `true` | 英語の機能語（`the`・`is`・`of`・`who` など）をキーワードに使わない。ありふれた語だけの質問が、ほとんどの記録に当たることがなくなる | `false` |
| `kw_only_min_terms` | `3` | 意味は近くないが、キーワードだけで当たった記録は、質問の語を 3 つ以上含むときだけ Top matches に入れる。足りなければ弱い候補として出ることはある | `0` |
| `top_matches_max` | `5` | Top matches を 5 件までにして、差し込みを短く保つ | `0`（`search_result_limit` まで） |
| `cross_lang_min_cos` | `0.80` | 日本語の質問で英語の記録を（またはその逆を）探せるようにする。質問と違う文字で書かれた記録のうち最も近い 1 件を、この近さ以上なら候補にする | `0` |

これらの設定は指示書（`N3MemoryCore_v1.9.1_Free_*.md`）にはないので、指示書から作り直したコードにはありません。指示書どおりの検索にするには、`~/.n3mc-free-antigravity/config.json` に `"vector_min_cos": 0.85, "fts_stopwords": false, "kw_only_min_terms": 0, "top_matches_max": 0, "cross_lang_min_cos": 0` と書きます。

### 弱い候補（min_results）

関連度の下限を通った記録が 3 件に満たないときは、下限で落ちた記録のうち近いものを、合計 3 件まで補います。補った記録は `## Possibly related (weak matches — may be unrelated)` という別の見出しの下に出し、Antigravity には「関係があるときだけ使う」と指示しています。記憶がまったく入らない質問がなくなる代わりに、毎ターン最大 3 件、多くは関係の薄い記録が増えます。補充をやめるときは `~/.n3mc-free-antigravity/config.json` に `"min_results": 0` と書きます。ほかの数にすると件数が変わります。

古い記録が、古いことを理由に検索から消えることはありません。古さは、同じ関連度の新しい記録より下に並べるためにだけ使います。

### バックアップと復元

記憶を別の環境に移行する場合や、安全のためにバックアップする場合は `~/.n3mc-free-antigravity/` 配下の以下の 2 ファイルを保管してください：
- `.memory/n3memory.db` — 記憶データ本体
- `config.json` — `owner_id`・`local_id` のUUIDv4キー

この 2 ファイルは、セットで保管してください。`config.json` には、DB の記録に付いている ID が入っています。

### アンインストール

方法 A で導入した場合は、Antigravity に「N3MemoryCore を削除してください」と頼んでください。フックの設定の解除も含めて行います。

自分で行うときは、次の順です。

1. `~/.gemini/config/hooks.json` から、`n3memorycore-free-antigravity` の登録を消し、Antigravity を再起動します。
2. 記憶のサーバーを止めます。サーバーは、バックグラウンドで動き続けています。コマンドラインに `n3memorycore_free_antigravity.n3memory --run-server` を含むプロセスを終わらせるか（PID は `~/.n3mc-free-antigravity/.memory/n3mc.pid` にあります）、PC を再起動します。
3. パッケージとデータを消します。

```bash
pip uninstall n3memorycore-free-antigravity
rm -rf ~/.n3mc-free-antigravity/                     # データ削除（不可逆）
```

4. プロジェクトのフォルダにある `.agents/rules/n3mc-behavior.md` と、`hooks.json` の隣にあるバックアップ `hooks.json.bak-n3mc-*` は、手で消してかまいません。

## ID 階層構造

N3MemoryCore は 6 つの ID フィールドで各レコードの出所と文脈を識別します：

| ID | 保存場所 | 生成タイミング | 粒度 | 用途 |
|---|---|---|---|---|
| `id` (PK) | DB レコード | レコード作成時 (UUIDv7, 時系列順) | **1 レコード** | 各記憶の一意識別子 |
| `owner_id` | `config.json` | 初回起動時 (UUIDv4) | **所有者 / データフォルダ** | データの所有者識別 |
| `local_id` | `config.json` / API | 初回起動時 (UUIDv4)、またはリクエスト毎 | **インストール** | 1 つのインストールに 1 つ。どのセッションでも同じ値。全レコードに保存する（Free 版ではランキングには使用されない） |
| `session_id` | Antigravity から渡される（フックの入力の `conversationId`） | 会話ごと | **1 つの会話** | 同じ会話の記憶をまとめる。`b_session` ランキングバイアス（一致=1.0、不一致=0.6）を駆動し、進行中の会話を、関係のない過去の会話より優先する |
| `turn_id` | DB レコード | あなたの発言を保存するとき (UUIDv4) | **1 つのやりとり** | 1 つの発言と、それに答える返答を結ぶ。`--show-turn` と `--recall-thread` に渡す |
| `agent_name` | DB レコード | 保存ごと (任意文字列) | **表示名** | 書いたものの人間可読なラベル（フックは `"antigravity"`）。`--buffer --agent-id <name>` はこのフィールドを入れる |

```
owner_id  (データフォルダ ~/.n3mc-free-antigravity と、その所有者)
  └── local_id  (インストール。どのセッションでも同じ)
        └── session_id  (Antigravity の 1 つの会話)
              └── turn_id  (1 つのやりとり: 1 つの発言と、その返答)
                    └── id  (1 件のレコード = 1 つのチャンク)

agent_name  (表示用のラベル。階層の外。フックは "antigravity")
```

## 動作環境

- **Antigravity**（必須。フック機能を使います）
- **Python 3.10+**
- **OS**: Windows 11・Ubuntu（動作確認済み）。macOS は対象外です

> Pythonが入っているか確認するには、ターミナルで `python --version` を実行してください。

## 拡張性

N3MemoryCoreは指示書（仕様書）を読ませて作るため、拡張も Antigravity に相談するだけで対応できます。指示書を Antigravity に読ませて「○○を追加して」と伝えます。カスタマイズするときは、指示書の場所を教えて「指示書も直してください」と伝えてください。

---

Apache License 2.0 — Copyright (C) 2026 NeuralNexusNote™ / ArnolfJp019
詳細は [LICENSE](./LICENSE) をご覧ください。
