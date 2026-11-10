# egov-data-mcp

政府のオープンデータを検索し、データセットの説明とCSVなどの配布URLを取得できます。読み取り専用で、APIキーの設定は不要です。[uv](https://docs.astral.sh/uv/) と Git が必要です。Python 3.12以上に対応しています。

## MCPクライアントに登録する

公開GitHubリポジトリから `uvx` で起動します。初回は依存関係の準備に時間がかかることがあります。

### Codex

```sh
codex mcp add egov-data-mcp -- uvx --python 3.12 --from git+https://github.com/koizumikento/egov-data-mcp.git@main egov-data-mcp
codex mcp list
```

`codex mcp list` で登録を確認し、Codexの新しいセッションで `/mcp` を開くと、接続状態を確認できます。[Codexの公式設定ガイド](https://learn.chatgpt.com/docs/extend/mcp?surface=cli)

Codexのデスクトップアプリでは、設定の「MCP servers」でSTDIOサーバーを追加し、下のJSON例と同じコマンド・引数を指定する方法もあります。

### Claude Desktop / Cursor

次のファイルに設定します。

- Claude Desktop（Windows） `%APPDATA%/Claude/claude_desktop_config.json`
- Claude Desktop（macOS） `~/Library/Application Support/Claude/claude_desktop_config.json`
- Cursor `.cursor/mcp.json`（プロジェクト内）

既に `mcpServers` がある場合は、その中にサーバーの項目を追加してください。保存後にクライアントを再起動し、ツールが表示されるか確認します。[設定ファイルの場所と接続手順](https://py.sdk.modelcontextprotocol.io/get-started/real-host/)

```json
{
  "mcpServers": {
    "egov-data-mcp": {
      "command": "uvx",
      "args": [
        "--python",
        "3.12",
        "--from",
        "git+https://github.com/koizumikento/egov-data-mcp.git@main",
        "egov-data-mcp"
      ]
    }
  }
}
```

`uvx` が見つからない場合は、設定のコマンドに実行ファイルの絶対パスを指定してください。

登録後は、チャットで次のように聞けます。

> 防災に関する政府のデータセットを3件探して、配布URLも教えて。

## ツール

| ツール | 用途 |
| --- | --- |
| `search_datasets` | キーワードでデータセットを検索 |
| `get_dataset` | データセットIDで詳細と配布先の一覧を取得 |

データセットのメタデータと配布URLを返します。配布ファイルの取得や内容の変換は別途行ってください。

## CLI

CLIやPythonライブラリを手元で使う場合は、リポジトリをクローンして準備します。

```sh
git clone https://github.com/koizumikento/egov-data-mcp.git
cd egov-data-mcp
uv sync --locked
```

```sh
uv run egov-data-mcp search-datasets --query "防災" --limit 1
uv run egov-data-mcp get-dataset --dataset-id cao_20140904_0477 --limit 1
```

結果は標準出力にUTF-8のJSONで出力します。コマンドの引数は `uv run egov-data-mcp search-datasets --help` で確認できます。

## Pythonライブラリ

パッケージをインストールしたPython環境で、下記の非同期関数を直接呼び出せます。

```python
import asyncio

from egov_data_mcp import search_datasets

result = asyncio.run(search_datasets(query="防災", limit=1))
print(result)
```

公開関数 `search_datasets`、`get_dataset` を利用できます。イベントループがある環境では、関数を直接 `await` します。

## 出典と利用条件

コードはMIT Licenseです。取得するデータの権利と利用条件は、API提供元と各データ提供機関の定めに従います。[公式API仕様](https://data.e-gov.go.jp/data/ja/api_guide) · [利用案内](https://www.e-gov.go.jp/info/ja/terms)

## 開発

```sh
uv sync --locked
uv run ruff check .
uv run ty check
uv run pytest
uv build
```
