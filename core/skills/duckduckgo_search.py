from core.skills.registry import BaseSkill
import asyncio
import urllib.request
import urllib.parse
import json
import logging

logger = logging.getLogger("zom.skills.duckduckgo_search")

class DuckDuckGoSearchSkill(BaseSkill):
    name = "duckduckgo_search"
    description = "DuckDuckGo üzerinden internette arama yapar ve güncel web sonuçlarını getirir."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Aranacak kelime veya cümle (örn: 'OpenAI GPT-4o')"
            }
        },
        "required": ["query"]
    }

    async def execute(self, query: str, **kwargs) -> str:
        try:
            # Önce kütüphaneyi dene
            try:
                from duckduckgo_search import DDGS
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=5))
                    if results:
                        formatted = []
                        for r in results:
                            title = r.get("title", "No Title")
                            href = r.get("href", "No Link")
                            body = r.get("body", "")
                            formatted.append(f"Title: {title}\nLink: {href}\nSnippet: {body}")
                        return "\n\n".join(formatted)
            except Exception as e:
                logger.warning(f"DDGS library failed: {e}. Falling back to HTML scraping...")

            # Kütüphane hata verirse veya boş dönerse HTML/Lite sürümünü kazı
            import re
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
            req = urllib.request.Request(url, headers=headers)

            def _fetch_html():
                with urllib.request.urlopen(req, timeout=10) as r:
                    return r.read().decode("utf-8")

            html = await asyncio.to_thread(_fetch_html)

            # HTML parser olmaksızın basit regex ile sonuçları bulmaya çalış
            snippets = re.findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
            titles = re.findall(r'<a class="result__a"[^>]*>(.*?)</a>', html, re.DOTALL)
            links = re.findall(r'<a class="result__url"[^>]*>(.*?)</a>', html, re.DOTALL)

            if not titles:
                snippets = re.findall(r'<td class="result-snippet"[^>]*>(.*?)</td>', html, re.DOTALL)
                titles = re.findall(r'<a class="result-link"[^>]*>(.*?)</a>', html, re.DOTALL)
                links = re.findall(r'<span class="result-url"[^>]*>(.*?)</span>', html, re.DOTALL)

            if not titles:
                logger.warning("Scraping DDG failed. Falling back to Wikipedia search...")
                wiki_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&utf8=&format=json"
                wiki_req = urllib.request.Request(wiki_url, headers=headers)

                def _fetch_wiki():
                    with urllib.request.urlopen(wiki_req, timeout=10) as r:
                        return json.loads(r.read().decode())

                data = await asyncio.to_thread(_fetch_wiki)
                wiki_results = data.get("query", {}).get("search", [])
                if wiki_results:
                    output = ["[Fallback Wikipedia Results]"]
                    for res in wiki_results[:3]:
                        snippet = re.sub('<[^<]+>', '', res['snippet'])
                        output.append(f"Title: {res['title']}\nSnippet: {snippet}")
                    return "\n\n".join(output)
                return f"No search results found for: {query}"

            output = []
            for i in range(min(len(titles), 5)):
                title = re.sub('<[^<]+>', '', titles[i]).strip()
                snippet = re.sub('<[^<]+>', '', snippets[i]).strip() if i < len(snippets) else ""
                link = re.sub('<[^<]+>', '', links[i]).strip() if i < len(links) else ""
                output.append(f"Title: {title}\nLink: {link}\nSnippet: {snippet}")

            return "\n\n".join(output)

        except Exception as e:
            return f"DuckDuckGo search error: {str(e)}"
