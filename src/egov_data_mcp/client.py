from __future__ import annotations

from typing import Annotated, Any

import httpx
from pydantic import Field, validate_call

BASE_URL = "https://data.e-gov.go.jp/data/api/action/"
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0, le=10000)]


def dataset_summary(dataset: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": dataset["id"],
        "title": dataset["title"],
        "publisher": (dataset.get("organization") or {}).get("title"),
        "updated_at": dataset.get("metadata_modified"),
        "license_id": dataset.get("license_id"),
        "source_url": f"https://data.e-gov.go.jp/data/ja/dataset/{dataset['name']}",
    }


async def get_response(path: str, **params: str | int | None) -> httpx.Response:
    query = {key: value for key, value in params.items() if value is not None}
    try:
        async with httpx.AsyncClient(base_url=BASE_URL, timeout=20.0) as client:
            response = await client.get(path, params=query)
            response.raise_for_status()
            return response
    except httpx.HTTPStatusError as exc:
        raise ValueError(f"Upstream HTTP error {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise ValueError("Could not reach the upstream API.") from exc


async def get_json(path: str, **params: str | int | None) -> dict[str, Any]:
    response = await get_response(path, **params)
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError("Upstream response was not a JSON object.")
    return data


@validate_call
async def search_datasets(query: Query, limit: Limit = 10, offset: Offset = 0) -> dict[str, Any]:
    """Search datasets by keyword. Use the returned ID to look up distribution files."""
    data = await get_json("package_search", q=query, rows=limit, start=offset)
    if data.get("success") is not True:
        raise ValueError("The e-Gov catalog reported a search error.")
    result = data["result"]
    return {
        "total": result["count"],
        "offset": offset,
        "datasets": [dataset_summary(item) for item in result["results"]],
    }


@validate_call
async def get_dataset(dataset_id: Query, limit: Limit = 10, offset: Offset = 0) -> dict[str, Any]:
    """Get a dataset and one page of its resources by CKAN ID or name."""
    data = await get_json("package_show", id=dataset_id)
    if data.get("success") is not True:
        raise ValueError("The e-Gov catalog reported a lookup error.")
    result = data["result"]
    resources = result.get("resources", [])
    return {
        **dataset_summary(result),
        "description": result.get("notes"),
        "total_resources": len(resources),
        "resource_offset": offset,
        "resources": [
            {key: item.get(key) for key in ("id", "name", "format", "url")}
            for item in resources[offset : offset + limit]
        ],
    }
