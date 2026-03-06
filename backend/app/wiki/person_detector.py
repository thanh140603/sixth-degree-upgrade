import logging
from typing import Set
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from app.core.settings import settings

logger = logging.getLogger(__name__)

_person_cache: dict[str, bool] = {}


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def _fetch_wikibase_item(title: str) -> str | None:
    url = "https://en.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "format": "json",
        "titles": title,
        "prop": "pageprops",
        "ppprop": "wikibase_item",
    }

    headers = {"User-Agent": settings.wiki_user_agent}

    with httpx.Client(timeout=10.0) as client:
        res = client.get(url, params=params, headers=headers)
        res.raise_for_status()
        data = res.json()

    pages = data.get("query", {}).get("pages", {})
    for page_id, page in pages.items():
        if page_id == "-1":
            continue
        pageprops = page.get("pageprops", {})
        item = pageprops.get("wikibase_item")
        if isinstance(item, str):
            return item

    return None


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
def _wikidata_is_human(qid: str) -> bool:
    if not qid or not qid.startswith("Q"):
        return False

    sparql_query = f"""
    ASK {{
      wd:{qid} wdt:P31 wd:Q5 .
    }}
    """

    url = "https://query.wikidata.org/sparql"
    headers = {
        "User-Agent": settings.wiki_user_agent,
        "Accept": "application/sparql-results+json",
    }
    params = {
        "format": "json",
        "query": sparql_query,
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            res = client.get(url, params=params, headers=headers)
            res.raise_for_status()
            data = res.json()

        if "boolean" in data:
            return data["boolean"]
        results = data.get("results", {}).get("bindings", [])
        return len(results) > 0
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404 or e.response.status_code >= 500:
            logger.warning("Wikidata query failed for %s: %s", qid, e)
            return False
        raise
    except Exception as e:
        logger.warning("Error querying Wikidata for %s: %s", qid, e)
        return False


def is_person_page(title: str, seed_names: Set[str] | None = None) -> bool:
    """
    Check if a Wikipedia page is about a person.
    
    Args:
        title: Wikipedia page title
        seed_names: Optional set of known person names (if provided, check this first)
    
    Returns:
        True if page is about a person, False otherwise
    """
    # Check cache first
    if title in _person_cache:
        return _person_cache[title]

    # If in seed list, definitely a person
    if seed_names and title in seed_names:
        _person_cache[title] = True
        return True

    # Check Wikipedia + Wikidata
    try:
        qid = _fetch_wikibase_item(title)
        if not qid:
            _person_cache[title] = False
            return False

        is_human = _wikidata_is_human(qid)
        _person_cache[title] = is_human
        return is_human

    except Exception as exc:
        logger.warning("Failed to check if %s is a person: %s", title, exc)
        _person_cache[title] = False
        return False


def clear_cache() -> None:
    """Clear the person detection cache (useful for testing)."""
    global _person_cache
    _person_cache.clear()
