# egov-data-mcp

政府のオープンデータを検索し、データセットの説明、CSVやPDFなどの配布URL、カタログの更新履歴を取得できます。読み取り専用で、APIキーの設定は不要です。[uv](https://docs.astral.sh/uv/) と Git が必要です。Python 3.12以上に対応しています。

[MCP登録](#mcpクライアントに登録する) · [CLI](#cliで使う) · [Pythonライブラリ](#pythonライブラリとして使う)

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

> 内閣府の防災データセットをPDFの配布があるものに絞って、見つかったデータセットの更新履歴も見せて。

## ツール

| ツール | 用途 |
| --- | --- |
| `search_datasets` | キーワードで検索。組織、配布形式、更新日で絞り込み可 |
| `get_dataset` | データセットIDで詳細と配布先の一覧を取得 |
| `search_resources` | 配布ファイル名で検索し、配布URLと親データセットのIDを取得 |
| `get_dataset_history` | データセットIDでカタログの更新イベントを取得 |

`search_datasets` の `organization` には組織名の代わりにカタログの組織IDを指定します。例えば内閣府は `org_0400` です。`file_format` には `PDF` や `CSV` を指定します。`updated_since` と `updated_until` は `YYYY-MM-DD` 形式で、UTCで指定日を含みます。組み合わせた条件をすべて満たすデータセットを返します。[組織一覧](https://data.e-gov.go.jp/data/ja/organization)

`search_resources` が返す `package_id` は `get_dataset` や `get_dataset_history` に渡せます。配布ファイルの取得や内容の変換は別途行ってください。各ツールは `limit`（1〜100、既定10）と `offset`（0〜10000、既定0）でページ送りできます。履歴に総件数はないため、返った件数が `limit` 未満なら最後のページです。履歴にはカタログのイベント日時と種別が含まれます。

## CLIで使う

CLIやPythonライブラリを手元で使う場合は、リポジトリをクローンして準備します。

```sh
git clone https://github.com/koizumikento/egov-data-mcp.git
cd egov-data-mcp
uv sync --locked
```

```sh
uv run egov-data-mcp search-datasets --query "防災" --organization org_0400 --format PDF --updated-since 2023-06-01 --limit 1
uv run egov-data-mcp get-dataset --dataset-id cao_20140904_0477 --limit 1
uv run egov-data-mcp search-resources --query "統計" --limit 1
uv run egov-data-mcp get-dataset-history --dataset-id cao_20140904_0477 --limit 1
```

結果は標準出力にUTF-8のJSONで出力します。コマンドの引数は `uv run egov-data-mcp search-datasets --help` で確認できます。

## Pythonライブラリとして使う

自分のPythonプロジェクト（`pyproject.toml` があるディレクトリ）で依存関係に追加します。

```sh
uv add "git+https://github.com/koizumikento/egov-data-mcp.git@main"
```

次のコードを `example.py` に保存し、同じディレクトリで `uv run python example.py` を実行します。

```python
import asyncio

from egov_data_mcp import get_dataset_history, search_datasets

async def main():
    result = await search_datasets("防災", limit=1, organization="org_0400", file_format="PDF")
    if result["datasets"]:
        dataset_id = result["datasets"][0]["id"]
        print(await get_dataset_history(dataset_id, limit=1))

asyncio.run(main())
```

上の表にある4ツールは、同名の非同期関数として利用できます。イベントループがある環境では、関数を直接 `await` します。

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
