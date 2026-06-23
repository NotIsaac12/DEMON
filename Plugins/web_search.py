# Плагин поиска информации в реальном времени
import os
from duckduckgo_search import DDGS

def web_search(query: str) -> str:
    """Ищет информацию в интернете в реальном времени через DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if not results:
                return "В интернете ничего не найдено."
            return "\n---\n".join([f"Сайт: {r['title']}\nСуть: {r['body'][:250].strip()}" for r in results])
    except Exception as e:
        return f"Ошибка поиска: {str(e)}"
