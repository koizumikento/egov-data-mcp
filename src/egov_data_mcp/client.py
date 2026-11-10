from __future__ import annotations

from datetime import date
from typing import Annotated, Any

import httpx
from pydantic import Field, validate_call

BASE_URL = "https://data.e-gov.go.jp/data/api/action/"
Query = Annotated[str, Field(min_length=1, max_length=200, pattern=r"\S")]
Limit = Annotated[int, Field(ge=1, le=100)]
Offset = Annotated[int, Field(ge=0, le=10000)]
Organization = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,100}$")]
FileFormat = Annotated[str, Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._+/ ()-]{0,49}$")]


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
async def search_datasets(
    query: Query,
    limit: Limit = 10,
    offset: Offset = 0,
    *,
    organization: Organization | None = None,
    file_format: FileFormat | None = None,
    updated_since: date | None = None,
    updated_until: date | None = None,
) -> dict[str, Any]:
    """Search datasets by keyword, optionally filtering by organization slug (e.g. org_0400),
    resource format (e.g. PDF), and inclusive UTC modification dates (YYYY-MM-DD).
    Use the returned ID to look up distribution files.
    """
    if updated_since and updated_until and updated_since > updated_until:
        raise ValueError("updated_since must be on or before updated_until.")
    filters = []
    if organization:
        filters.append(f'organization:"{organization}"')
    if file_format:
        filters.append(f'res_format:"{file_format.upper()}"')
    if updated_since or updated_until:
        start = f"{updated_since}T00:00:00Z" if updated_since else "*"
        end = f"{updated_until}T23:59:59.999Z" if updated_until else "*"
        filters.append(f"metadata_modified:[{start} TO {end}]")
    data = await get_json(
        "package_search", q=query, rows=limit, start=offset, fq=" AND ".join(filters) or None
    )
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


@validate_call
async def search_resources(query: Query, limit: Limit = 10, offset: Offset = 0) -> dict[str, Any]:
    """Search distribution files by resource name. Use package_id to get the parent dataset."""
    data = await get_json("resource_search", query=f"name:{query}", limit=limit, offset=offset)
    if data.get("success") is not True:
        raise ValueError("The e-Gov catalog reported a resource search error.")
    result = data["result"]
    return {
        "total": result["count"],
        "offset": offset,
        "resources": [
            {key: item.get(key) for key in ("id", "package_id", "name", "format", "url")}
            for item in result["results"]
        ],
    }


@validate_call
async def get_dataset_history(
    dataset_id: Query, limit: Limit = 10, offset: Offset = 0
) -> dict[str, Any]:
    """Get one page of catalog update events for a dataset ID or CKAN name."""
    data = await get_json("package_activity_list", id=dataset_id, limit=limit, offset=offset)
    if data.get("success") is not True:
        raise ValueError("The e-Gov catalog reported a history lookup error.")
    return {
        "offset": offset,
        "activities": [
            {key: item.get(key) for key in ("id", "timestamp", "activity_type", "object_id")}
            for item in data["result"][:limit]
        ],
    }
