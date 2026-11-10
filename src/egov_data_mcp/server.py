from mcp.server import MCPServer
from mcp.types import ToolAnnotations

from .client import get_dataset, search_datasets

READ_ONLY = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, destructive_hint=False, open_world_hint=True
)


def create_server() -> MCPServer:
    mcp = MCPServer("egov-data-mcp")
    mcp.tool(annotations=READ_ONLY)(search_datasets)
    mcp.tool(annotations=READ_ONLY)(get_dataset)
    return mcp
