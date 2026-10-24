[Русский](README.md) | [English](README.en.md) | **日本語**

> この翻訳はAIによる機械翻訳で、日本語話者による確認はまだ行われていません。(Перевод выполнен ИИ, носителем языка не проверен.)

# SVOD-1

**SVOD-1**(СВОД-1)は、Standards(標準)、Versions(バージョン)、Descriptions(記述)、Discipline(規律)の頭文字をとったロシア語の略称です(キリル文字で「СВОД」と書きます)。技術名は `armarium-linux-cli-plugin` です。

**名前について。** コマンド、パス、スキル名では、このプラグインは `armarium` と呼ばれます(`/armarium:run-audit`、`~/.claude/armarium.json`、`armarium@vugsk-plugins`)。これは技術名であり、変更されません。SVOD-1 と `armarium` は同じプラグインです。

個人用の Claude Code プラグイン SVOD-1(コードワードは `armarium`、ラテン語で「道具箱」の意味)です。自分の標準に沿って作業するための19個のスキル(うち2つは手動で実行するチェック)と、監査を思い出させるフックが入っています。

> スキルが扱う標準や、スキル本文の一部はロシア語で書かれています。このページはロシア語版 README の翻訳です。

## 何のためのものか

自分の標準に沿ったプロジェクト作業を支援します。プロジェクトとデバイスの命名、終了基準つきの6つのプロジェクト段階、ノート(アイデア、要件、設計、マイルストーン付き計画、決定事項)、テスト、セキュリティと依存関係の確認、振り返りが対象です。一部のスキルはコード、ファームウェア、ハードウェアのメンターで、説明はしますがコードは利用者自身が書きます。標準はあなたの Obsidian の保管庫(vault)に置かれます。標準がない場合は、`setup` ウィザードが質問をして下書きを作ります。

## 必要なもの

Linux 上の Claude Code 2.1.310 で動作を確認しました。`python3`、`bash`、`jq`、`git`、`claude` が必要です。外部ライブラリはありません(Python の標準ライブラリのみ)。

## 内容

| フォルダ | 説明 |
| --- | --- |
| `skills/` | 19個のスキル:プロジェクトの命名と段階、コード・ファームウェア・ハードウェアのメンター、基板チェック、テスト、セキュリティ、依存関係、リバースエンジニアリング、プロジェクトの振り返り、標準の監査、`setup` ウィザード、手動実行の `run-audit`(整合性チェック)と `run-trigger-check`(スキルの起動チェック。アカウントのトークンを消費し、確認を求めます) |
| `docs/` | スキル用の資料:`settings.md`(設定ファイル `~/.claude/armarium.json`)、`standards-contract.md`(ウィザードが使う標準の構造の取り決め) |
| `hooks/` | `audit-reminder.sh` と `hooks.json`:標準やスキルを編集した後に、`standards-audit` の実行とコピーの更新を促します |
| `checks/` | チェック一式:`queries.json`、`run_trigger.py`、`make_fixtures.py`、説明とシナリオ |
| `tools/` | `make_vault_copy.py`(Obsidian の保管庫へのコピーと説明。プラグインの作者向け) |
| `tests/` | プラグインのテスト(実行方法は「開発者向け」を参照) |

標準(`Стандарт по названию проектов.md`、`Стандарт по названию устройств.md`、`Стандарт проектных заметок.md`)はプラグインではなく、保管庫の `Проекты/` フォルダにあります(保管庫のルートは `~/.claude/armarium.json` で指定します)。スキルはそこから読み込みます。

## GitHub からのインストール

このリポジトリ自体がマーケットプレイスです(`.claude-plugin/marketplace.json`、名前は `vugsk-plugins`):

```
claude plugin marketplace add vugsk/armarium-linux-cli-plugin
claude plugin install armarium@vugsk-plugins
```

インストール後に「настрой armarium」(armarium を設定して)と伝えると、`setup` ウィザードが設定ファイルと標準の下書きを作ります。

## 開発者向け:フォルダから接続する

ローカルのマーケットプレイス経由で、フォルダをそのまま読み込めます:

1. プラグインを検証します:`claude plugin validate <プラグインのフォルダ>`。インストールせずに試す場合は `claude --plugin-dir <プラグインのフォルダ>`。
2. プラグインのフォルダの隣に `.claude-plugin/marketplace.json` を置きます(名前、`owner`、マーケットプレイスのルートからの `source` 「./<プラグインのフォルダ>」を持つプラグインの項目)。その後 `claude plugin marketplace add <マーケットプレイスのルート>`、続けて `claude plugin install armarium@<マーケットプレイス名>` を実行します。プラグインの変更はセッションの再起動か `/reload-plugins` で反映され、バージョンを変える必要はありません。
3. 以前、同じスキルが `~/.claude/skills` にあった場合は、そこから取り除いてください(アーカイブへ移動)。残すと二重に表示されます。スキル名は `armarium:<スキル>` になります。

## 推奨プラグイン

公式カタログ `claude-plugins-official` の次のプラグインと一緒に SVOD-1 を使えます。作者が1台のマシンで確認したものです。SVOD-1 自体がどれだけ良くなるかは測っていないため、保証ではなく推奨です。

| プラグイン | 目的 | プラグイン以外に必要なもの |
| --- | --- | --- |
| `clangd-lsp`, `rust-analyzer-lsp`, `pyright-lsp`, `gopls-lsp`, `jdtls-lsp` | 言語サーバー:Claude が C/C++、Rust、Python、Go、Java のコードをより正確に読めるようになり、`code-coach` スキルに役立ちます | サーバー本体がシステムに必要:`clangd`、`rust-analyzer`、`pyright`、`gopls`、`jdtls`。サーバーがないとプラグインは何もしません |
| `context7` | バージョンごとの最新のライブラリ文書。「事実は文書からのみ」という規則を支えます | リクエストは外部サーバー `mcp.context7.com` に送られます。非公開のコードを送らないでください |
| `security-guidance` | 編集時に安全でないパターンを警告し、停止時に変更を確認します。`project-security` スキルを補います | フックが編集のたびに動くため、通知が多くなることがあります。無効化は `claude plugin disable security-guidance@claude-plugins-official` |

インストール:`claude plugin install <名前>@claude-plugins-official`。インストール済みのプラグインは `claude plugin list` で確認できます。

## 既知の制限

- 保管庫へのパスは `~/.claude/armarium.json`(フィールド `vault`、`docs/settings.md` を参照)から取得されます。保管庫内の構成は固定です(`Проекты/`、`Документация/Скиллы Claude/`)。設定ファイルと不足している標準の下書きはウィザードが作ります。「настрой armarium」と伝えてください(スキル `setup`)。ウィザードが設定できるのは辞書、種類のグループ、段階の基準、命名規則だけです。それ以外の取り決め(ノート名、段階、タグの形式)はスキルに組み込まれており、`docs/standards-contract.md` に一覧があります。
- プラグイン内でのスキルの起動(`armarium:` の接頭辞つき)は73件のクエリで確認しました。直近の全件実行は71/73で、2件のクエリは安定して起動しません(経費管理の新しいプログラムについての依頼での `project-stages`、「python で関数を書いて」での `code-coach`)。実行は `/armarium:run-trigger-check`(トークンを消費します)。
- スキルは保管庫のファイルを読み込みますが、その中の文章は指示ではなくデータとして扱われます(`docs/settings.md`)。確認は2回の試行だけで、指示の差し込みに対する完全な防御の証明ではありません。
- ライセンス:MIT、著作権者は `vugsk`(ファイル `LICENSE`、`plugin.json` の `license` フィールド)。

## 開発者向け

スキルの正本はこのリポジトリです。作者の保管庫にあるバックアップコピーとスキルの説明(`~/.claude/armarium.json` の保管庫内の `Документация/Скиллы Claude/`)は、ここから生成されます:

```
python3 -I tools/make_vault_copy.py --yes
```

テスト(Python の標準ライブラリのみ、トークンは消費しません):

```
python3 -m unittest discover -s tests -v
```

ウィザードの3つのシナリオ(`tests/test_09_wizard_scenarios.py`)は、既定ではスキップされます。`claude -p` を実行してトークンを消費し、実際の `~/.claude/armarium.json` を一時的に差し替えるためです(バックアップと復元つき)。有効にするには環境変数 `ARMARIUM_WIZARD_TEST=1` を設定します。スキルの起動チェックは `/armarium:run-trigger-check` です(こちらもトークンを消費します)。
