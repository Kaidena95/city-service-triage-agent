"""
test_mcp.py — Manual test script for MCP tools

This simulates what an AI agent does when it calls your MCP tools.
Run this with the FastAPI server running in another terminal.

Usage:
    cd mcp
    python3 test_mcp.py
"""

import asyncio
import httpx


API_BASE = "http://127.0.0.1:8000"


async def simulate_list_requests(filters={}):
    """Simulates the list_requests MCP tool call"""
    print(f"\n{'='*50}")
    print(f"TOOL: list_requests | filters: {filters}")
    print('='*50)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/requests", params=filters)
        requests = response.json()

        if not requests:
            print("No requests found.")
            return

        for r in requests:
            print(f"ID:{r['id']} | {r['category']} | "
                  f"{r['priority']} | {r['status']}")
            print(f"  → {r['description'][:60]}")
            print(f"  → Action: {r['recommended_action'][:60]}")


async def simulate_get_request(request_id: int):
    """Simulates the get_request MCP tool call"""
    print(f"\n{'='*50}")
    print(f"TOOL: get_request | id: {request_id}")
    print('='*50)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE}/requests/{request_id}")

        if response.status_code == 404:
            print(f"Request #{request_id} not found.")
            return

        r = response.json()
        print(f"Request #{r['id']}: {r['description']}")
        print(f"Category: {r['category']} | Priority: {r['priority']}")
        print(f"Status: {r['status']}")
        print(f"Recommended Action: {r['recommended_action']}")


async def simulate_update_status(request_id: int, status: str):
    """Simulates the update_request_status MCP tool call"""
    print(f"\n{'='*50}")
    print(f"TOOL: update_request_status | id:{request_id} status:{status}")
    print('='*50)

    async with httpx.AsyncClient() as client:
        response = await client.patch(
            f"{API_BASE}/requests/{request_id}/status",
            params={"status": status}
        )

        if response.status_code == 404:
            print(f"Request #{request_id} not found.")
            return

        r = response.json()
        print(f"Updated Request #{r['id']} → status: {r['status']}")


async def main():
    print("\n🤖 MCP TOOL SIMULATION")
    print("Simulating what an AI agent would call...\n")

    # Test 1 — List all requests
    await simulate_list_requests()

    # Test 2 — List only critical safety requests
    await simulate_list_requests({"category": "safety", "priority": "critical"})

    # Test 3 — Get one specific request
    await simulate_get_request(1)

    # Test 4 — Update status
    await simulate_update_status(1, "in_progress")

    # Test 5 — Confirm status changed
    await simulate_get_request(1)

    print("\n✅ All MCP tool simulations complete.")


if __name__ == "__main__":
    asyncio.run(main())
    