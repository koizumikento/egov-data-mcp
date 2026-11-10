import json
import sys

import httpx
import pytest
import respx
from mcp import Client, StdioServerParameters
from mcp.types import TextContent

from egov_data_mcp import create_server
from egov_data_mcp.server import BASE_URL


@pytest.mark.asyncio
async def test_stdio_tools() -> None:
    params = StdioServerParameters(command=sys.executable, args=["-m", "egov_data_mcp"])
    async with Client(params, mode="legacy", read_timeout_seconds=10) as client:
        result = await client.list_tools()
    assert {tool.name for tool in result.tools} == {"search_datasets", "get_dataset"}
    assert all(tool.annotations and tool.annotations.read_only_hint for tool in result.tools)


@pytest.mark.asyncio
@respx.mock
async def test_tool_response() -> None:
    route = respx.get(BASE_URL + "package_show?id=test").mock(
        return_value=httpx.Response(
            200,
            json=json.loads(
                '{"success":true,"result":{"id":"test","title":"Test","name":"test","resources":[{"id":"first"},{"id":"second"}]}}'
            ),
        )
    )
    async with Client(create_server()) as client:
        result = await client.call_tool(
            "get_dataset", {"dataset_id": "test", "limit": 1, "offset": 1}
        )
    assert route.called
    assert not result.is_error
    assert isinstance(result.content[0], TextContent)
    payload = json.loads(result.content[0].text)
    assert payload["total_resources"] == 2
    assert payload["resources"][0]["id"] == "second"
