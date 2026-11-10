from datetime import date

import httpx
import pytest
import respx

from egov_data_mcp import get_dataset_history, search_datasets, search_resources
from egov_data_mcp.client import BASE_URL


@pytest.mark.asyncio
@respx.mock
async def test_dataset_filters_preserve_search_output() -> None:
    route = respx.get(BASE_URL + "package_search").respond(
        json={
            "success": True,
            "result": {"count": 1, "results": [{"id": "a", "name": "a", "title": "防災"}]},
        },
    )
    result = await search_datasets(
        "防災",
        1,
        5,
        organization="org_0400",
        file_format="pdf",
        updated_since=date(2023, 6, 1),
        updated_until=date(2023, 6, 1),
    )
    assert dict(route.calls.last.request.url.params) == {
        "q": "防災",
        "rows": "1",
        "start": "5",
        "fq": 'organization:"org_0400" AND res_format:"PDF" AND '
        "metadata_modified:[2023-06-01T00:00:00Z TO 2023-06-01T23:59:59.999Z]",
    }
    assert result == {
        "total": 1,
        "offset": 5,
        "datasets": [
            {
                "id": "a",
                "title": "防災",
                "publisher": None,
                "updated_at": None,
                "license_id": None,
                "source_url": "https://data.e-gov.go.jp/data/ja/dataset/a",
            }
        ],
    }


@pytest.mark.asyncio
@respx.mock
async def test_resource_search_returns_parent_dataset_id() -> None:
    route = respx.get(BASE_URL + "resource_search").respond(
        json={
            "success": True,
            "result": {
                "count": 3,
                "results": [
                    {
                        "id": "r",
                        "package_id": "d",
                        "name": "統計",
                        "format": "CSV",
                        "url": "https://example.com/data.csv",
                    }
                ],
            },
        },
    )
    result = await search_resources("統計", 1, 2)
    assert dict(route.calls.last.request.url.params) == {
        "query": "name:統計",
        "limit": "1",
        "offset": "2",
    }
    assert result["total"] == 3
    assert result["offset"] == 2
    assert result["resources"][0]["package_id"] == "d"


@pytest.mark.asyncio
@respx.mock
async def test_history_requests_one_page_and_excludes_raw_snapshots() -> None:
    event = {
        "id": "first",
        "timestamp": "2023-06-01T21:37:05",
        "activity_type": "changed package",
        "object_id": "dataset",
    }
    route = respx.get(BASE_URL + "package_activity_list?id=dataset&limit=1&offset=2").mock(
        return_value=httpx.Response(
            200,
            json={
                "success": True,
                "result": [{**event, "data": {"package": {}}, "user_id": "author"}, event],
            },
        ),
    )
    assert await get_dataset_history("dataset", 1, 2) == {"offset": 2, "activities": [event]}
    assert route.called
