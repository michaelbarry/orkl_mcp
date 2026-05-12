import httpx
from fastmcp import FastMCP
from pydantic import Field
from typing import Optional, List, Dict

# 1. Initialize FastMCP - the high-level framework
mcp = FastMCP(
    "ORKL-Threat-Intel",
    instructions="I provide access to the ORKL threat intelligence library. Use me to search for reports, actors, and detailed indicator data."
)

ORKL_BASE = "https://orkl.eu/api/v1"

# 2. Define a robust search tool
@mcp.tool()
async def search_threat_reports(query: str, limit: int = 10) -> str:
    """
    Search ORKL for threat reports based on a keyword, malware name, or actor.
    Returns a formatted list of matching reports with their IDs.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # /library/entries silently ignores `q` — must use /library/search?query=
        params = {"query": query, "limit": limit}
        response = await client.get(f"{ORKL_BASE}/library/search", params=params)
        response.raise_for_status()

        data = response.json().get("data") or []
        if not data:
            return f"No results found for '{query}'."

        output = [f"Found {len(data)} reports:"]
        for entry in data:
            title = entry.get("title") or "(untitled)"
            output.append(f"ID: {entry['id']} | Title: {title} | Date: {entry.get('created_at', 'N/A')}")

        return "\n".join(output)

# 3. Define a deep-dive detail tool
@mcp.tool()
async def get_report_details(report_id: str) -> Dict:
    """
    Fetch full JSON metadata for a specific ORKL report ID. 
    Useful for extracting IOCs, file hashes, and target information.
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{ORKL_BASE}/library/entry/{report_id}")
        response.raise_for_status()
        return response.json().get("data", {})

# 4. Define a tool for Threat Actor profiles
@mcp.tool()
async def get_threat_actor_info(name_or_id: str) -> str:
    """
    Get detailed profile information for a threat actor (e.g., 'Lazarus Group' or 'APT28').
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First list actors to find a match
        response = await client.get(f"{ORKL_BASE}/ta/entries")
        response.raise_for_status()
        actors = response.json().get("data", [])
        
        # Look for a name match
        match = next((a for a in actors if name_or_id.lower() in a['main_name'].lower() or name_or_id == a['id']), None)
        
        if not match:
            return f"No actor found matching '{name_or_id}'."
            
        # Get details for the specific match
        detail_resp = await client.get(f"{ORKL_BASE}/ta/entry/{match['id']}")
        detail_resp.raise_for_status()
        details = detail_resp.json().get("data", {})
        
        res = [f"Name: {details.get('main_name')}", f"ID: {details.get('id')}"]
        if details.get('synonyms'):
            res.append(f"Aliases: {', '.join(details['synonyms'])}")
        
        return "\n".join(res)

if __name__ == "__main__":
    mcp.run()