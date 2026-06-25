from core.skills.registry import BaseSkill
import asyncio
import urllib.request
import urllib.parse
import json

class WebSearchSkill(BaseSkill):
    name = "web_search"
    description = "Wikipedia üzerinden internette arama yapar ve özet bilgi getirir."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Aranacak kelime (örn: Artificial Intelligence)"
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, **kwargs) -> str:
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})

            def _fetch():
                with urllib.request.urlopen(req, timeout=10) as r:
                    return json.loads(r.read().decode())

            data = await asyncio.to_thread(_fetch)
            results = data.get("query", {}).get("search", [])
            if not results:
                return f"No results found for '{query}'"

            import re
            output = []
            for res in results[:3]:
                snippet = re.sub('<[^<]+>', '', res['snippet'])
                output.append(f"Title: {res['title']}\nSnippet: {snippet}")

            return "\n\n".join(output)
        except Exception as e:
            return f"Search failed: {e}"
