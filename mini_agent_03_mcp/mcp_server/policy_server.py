"""8011 포트에서 독립 실행되는 호텔 정책 Streamable HTTP MCP Server입니다."""

import os
from typing import Literal

from mcp.server.fastmcp import FastMCP


POLICY_MCP_HOST = os.getenv("POLICY_MCP_HOST", "0.0.0.0")
POLICY_MCP_PORT = int(os.getenv("POLICY_MCP_PORT", "8011"))

mcp = FastMCP(
    "mini-agent-policy",
    instructions="호텔 ID로 체크인 및 취소 정책을 제공합니다.",
    host=POLICY_MCP_HOST,
    port=POLICY_MCP_PORT,
    stateless_http=True,
    json_response=True,
)


@mcp.tool()
def get_hotel_policy(
    hotel_id: Literal["hotel-busan-001", "hotel-seoul-001"],
) -> dict:
    """호텔 검색 결과의 hotel_id로 체크인 및 취소 정책을 조회합니다."""
    policies = {
        "hotel-busan-001": {
            "hotel_name": "바다 호텔",
            "check_in": "15:00",
            "check_out": "11:00",
            "cancellation": "체크인 2일 전까지 무료 취소",
        },
        "hotel-seoul-001": {
            "hotel_name": "도시 호텔",
            "check_in": "15:00",
            "check_out": "11:00",
            "cancellation": "체크인 1일 전까지 무료 취소",
        },
    }
    return {
        "hotel_id": hotel_id,
        **policies[hotel_id],
        "source": "hotel-policy-service",
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
