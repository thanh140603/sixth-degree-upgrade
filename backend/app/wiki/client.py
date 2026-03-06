import logging
from typing import List

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.settings import settings

logger = logging.getLogger(__name__)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
def fetch_outbound_titles(page_title: str) -> List[str]:
    """
    Fetch outbound article links for a Wikipedia page.
    Simplified version based on the Go implementation.
    """
    base_url = (
        "https://en.wikipedia.org/w/api.php?"
        "action=query&prop=links&format=json&plnamespace=0&pllimit=max&titles={title}"
    )

    all_titles: list[str] = []
    plcontinue: str | None = None

    with httpx.Client(timeout=30.0) as client:
        while True:
            url = base_url.format(title=httpx.QueryParams({"": page_title})[""])
            params = {}
            if plcontinue:
                params["plcontinue"] = plcontinue

            headers = {
                "User-Agent": settings.wiki_user_agent,
            }
            res = client.get(url, params=params, headers=headers)
            res.raise_for_status()

            data = res.json()
            pages = data.get("query", {}).get("pages", {})
            for _, page in pages.items():
                for link in page.get("links", []) or []:
                    if link.get("ns") == 0 and "title" in link:
                        all_titles.append(link["title"])

            cont = data.get("continue", {})
            plcontinue = cont.get("plcontinue")
            if not plcontinue:
                break

    return sorted(set(all_titles))

