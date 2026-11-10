# egov-data-mcp

e-Govデータポータルの公式APIを参照する読み取り専用のMCPサーバーです。Python 3.12以上とuv（0.13.4で検証）を使います。上流APIのキー設定は不要です。

## MCPクライアント設定

GitHubリポジトリへのアクセス権がある環境でクローンします。

```sh
git clone https://github.com/koizumikento/egov-data-mcp.git
cd egov-data-mcp
uv sync --locked
```

クライアントの設定に、クローン先の絶対パスを指定します。

```json
{
  "mcpServers": {
    "egov-data-mcp": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/egov-data-mcp", "run", "--locked", "egov-data-mcp"]
    }
  }
}
```

## ツール

| ツール | 用途 |
| --- | --- |
| `search_datasets` | キーワードでデータセットを検索 |
| `get_dataset` | データセットIDで詳細と配布先の一覧を取得 |

データセットのメタデータと配布URLを返します。配布ファイルの取得や内容の変換は別途行ってください。

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
