<!-- readme-header:start -->

<p align="center">
  <img src="./assets/readme/logo.svg" width="112" alt="Server Ops">
</p>

<h1 align="center">Server Ops</h1>

<p align="center">
  <strong>Agent が SSH でサーバーを調査し、承認されたデプロイ・保守作業と結果確認を行う Skill。</strong>
</p>

<p align="center">
  <a href="./README.md">中文</a> · <a href="./README.en.md">English</a> · <strong>日本語</strong> | <a href="./references/usage.md">文档</a> | <a href="./CONTRIBUTING.md">贡献</a> | <a href="https://github.com/CheshireMew/server-ops/issues">反馈</a>
</p>

<p align="center">
  <a href="https://x.com/0xCheshire" title="X"><img src="https://img.shields.io/badge/X-%400xCheshire-000000?logo=x&amp;logoColor=white" alt="X：@0xCheshire"></a>
  <a href="https://t.me/CheshireBTC" title="Telegram"><img src="https://img.shields.io/badge/Telegram-CheshireBTC-26A5E4?logo=telegram&amp;logoColor=white" alt="Telegram：CheshireBTC"></a>
  <a href="https://blog.blacknico.com/" title="Blog"><img src="https://img.shields.io/badge/Blog-blog.blacknico.com-2E7D32?logo=rss&amp;logoColor=white" alt="博客：blog.blacknico.com"></a>
  <a href="https://blacknico.com/" title="Homepage"><img src="https://img.shields.io/badge/Home-blacknico.com-1F6FEB?logo=googlechrome&amp;logoColor=white" alt="个人主页：blacknico.com"></a>
</p>

<p align="center">
  <a href="https://github.com/CheshireMew/server-ops/stargazers"><img src="https://img.shields.io/github/stars/CheshireMew/server-ops?style=flat" alt="GitHub Stars"></a>
  <a href="https://github.com/CheshireMew/server-ops/forks"><img src="https://img.shields.io/github/forks/CheshireMew/server-ops?style=flat" alt="GitHub Forks"></a>
  <a href="https://github.com/CheshireMew/server-ops/blob/HEAD/LICENSE"><img src="https://img.shields.io/github/license/CheshireMew/server-ops?style=flat" alt="Repository License"></a>
</p>

<!-- readme-header:end -->

Server Ops は、外部 Agent が SSH 経由でサーバーを運用するための Agent Skill です。対象のサーバーとプロジェクト、行いたい作業を伝えると、Agent が調査し、承認された操作を実行して、サーバーの実際の状態から結果を確認します。ログイン情報はローカルのツールが保存・使用するため、普段の依頼ではサーバーの別名を指定できます。

## Agent に作業を依頼する

[SKILL.md](./SKILL.md) を読み込み、アカウントを設定したら、次のように依頼できます。

```text
$server-ops prod の稼働状況を確認し、対処が必要な問題を報告してください。
```

| 作業 | 依頼例 | 得られる結果 |
| --- | --- | --- |
| サービスとログの調査 | prod の nginx と直近 50 件のログを確認し、エラーの原因を調べてください。 | 現在の状態、関連する根拠、未確認の点 |
| デプロイや更新 | prod の指定プロジェクトについて、バージョン・設定・起動方法を確認し、更新案を出してください。 | 承認用の具体的な計画と、承認後の実行・動作確認 |
| 設定変更や保守 | prod の nginx の設定を確認し、必要な変更と確認方法を説明してください。 | 変更範囲と影響、承認後の実施と結果確認 |

デプロイ、設定変更、削除、インストール、再起動などの前には、対象サーバー・範囲・影響を説明し、その計画への承認を得ます。承認された同じ計画内では、コマンドごとに確認を繰り返さず作業を進めます。

## 使い始める

ローカルツールは現在 **Windows** 向けで、**Python 3.10 以降、Paramiko、Tkinter** が必要です。リモートコマンドの例は Linux 向けです。実際のコマンドは対象サーバーに合わせて選びます。

### 1. Skill を取得して読み込む

```powershell
git clone https://github.com/CheshireMew/server-ops.git D:\Tools\agent-skills\server-ops
Set-Location D:\Tools\agent-skills\server-ops
$serverOpsRoot = (Get-Location).Path
```

対応する Agent の導入方法に従い、このディレクトリの `SKILL.md` を読み込ませてください。ツールを PowerShell から直接呼び出すこともできます。

### 2. ローカル環境を設定する

Paramiko と Tkinter をインポートできる Python を用意します。以下のパスは例なので、実際の環境に合わせて変更してください。

```powershell
& 'D:\Tools\Python310\python.exe' -m pip install paramiko
& 'D:\Tools\Python310\python.exe' -c 'import paramiko, tkinter'
New-Item -ItemType Directory -Path "$serverOpsRoot\.local" -Force | Out-Null
```

`.local/config.json` を作成し、Python、SSH ホスト記録ファイル、既定のサーバー別名を設定します。

```json
{
  "version": 1,
  "python_executable": "D:/Tools/Python310/python.exe",
  "known_hosts": "D:/Tools/ssh/known_hosts",
  "default_server": "prod"
}
```

`known_hosts` には、対象サーバーの確認済み公開鍵が記録された既存のファイルを指定します。未知のホストや鍵が一致しないホストへの接続は拒否されるため、初回接続前に公開鍵を確認して記録を用意してください。

### 3. アカウントを保存し、接続を確認する

```powershell
& "$serverOpsRoot\server-ops.ps1" setup --server prod --host ssh.example.com
& "$serverOpsRoot\server-ops.ps1" status --server prod
& "$serverOpsRoot\server-ops.ps1" exec --server prod --command 'hostname; whoami; date -Is'
```

例のアドレスを実際のアドレスに置き換え、ウィンドウでポート・ユーザー名・パスワードを入力します。`status` はローカルの保存状態を確認するだけです。最後のコマンドで SSH 接続し、`exit_code` が `0`、`stdout` のホスト・ユーザー・時刻が想定どおりであることを確認します。

既定アカウントを編集するには、[打开服务器账号填写窗口.cmd](./打开服务器账号填写窗口.cmd) をダブルクリックします。既存アカウントのパスワードを空欄にすると、保存済みのパスワードが維持されます。

## よく使うコマンド

共通の入口は `server-ops.ps1` です。上記の `$serverOpsRoot` を使って呼び出します。

| コマンド | 用途 |
| --- | --- |
| `list` | 保存済みのサーバーを一覧表示 |
| `status --server prod` | ローカルのアカウント情報を確認 |
| `setup --server prod --host ssh.example.com` | アカウントを追加・更新 |
| `exec --server prod --command 'uptime'` | SSH 経由でコマンドを実行 |
| `exec --server prod --script <ローカルスクリプトのパス>` | UTF-8 スクリプトを読み、その内容をリモートで実行 |

`--server` を省略すると `default_server` が使われます。実行タイムアウトは既定で 30 秒、変更する場合は `--timeout 60` を指定します。長いスクリプトは Skill 内の `.runs` に保存してください。詳しい例は [ツールの使用方法](./references/usage.md) を参照してください。詳細な作業文書は現在中国語です。

`list`、`status`、`exec` は JSON を返します。実行結果には `server`、`host`、`username`、`exit_code`、`stdout`、`stderr`、`approval_provided` が含まれます。識別できる照会はそのまま実行し、承認が必要な操作や判断できない構文は SSH 接続前に `approval_required: true` と終了コード `3` を返します。承認の扱いは [SKILL.md](./SKILL.md) を参照してください。

タイムアウトで SSH チャネルが閉じても、リモートの処理が続いている場合があります。再実行する前にサーバーの状態を確認してください。

## ファイルの保存先

| 場所 | 内容 |
| --- | --- |
| [SKILL.md](./SKILL.md) | Agent の作業手順、承認、完了条件 |
| [references/usage.md](./references/usage.md) | 設定、コマンド、結果の詳細 |
| `scripts/` | SSH ツール、コマンド確認、ローカルテスト |
| `.local/` | ローカル設定、暗号化アカウント、サーバーメモ。Git 対象外 |
| `.runs/` | 作業スクリプト、診断資料、ログのコピー。Git 対象外 |

保存先は常に Skill 自身の場所から決まり、呼び出し元の作業ディレクトリには左右されません。アカウントは保存時の Windows ユーザーに対して暗号化されるため、別の PC や Windows アカウントでは再入力が必要です。SSH 出力は既定で呼び出し元へ返し、記録が必要なときに `.runs` へ保存します。

## 開発への参加

変更と確認の方法は [CONTRIBUTING.md](./CONTRIBUTING.md)、不具合や提案の連絡先は [Issues](https://github.com/CheshireMew/server-ops/issues) です。

## ライセンス

**MPL-2.0** を採用しています。適用範囲と外部依存関係は [LICENSING.md](./LICENSING.md)、全文は [LICENSE](./LICENSE) を参照してください。
