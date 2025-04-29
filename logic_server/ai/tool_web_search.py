import os
from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def web_search(query: str) -> str:
    """
    Perform a web search using OpenAI's web_search_preview tool (gpt-4o).
    Returns a formatted string with results or error message.
    """
    query = query.strip()
    if not query:
        return "Error: No query provided."

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return "Error: OpenAI API key not found in environment."
    try:
        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model="gpt-4o",
            tools=[{"type": "web_search_preview"}],
            input=query,
        )
        output = getattr(response, "output_text", None) or str(response)
        if not output:
            return "No search results found for the query."
        return (
            f"# Web Search Results for: {query}\n\n{output}\n\nSearch performed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    except Exception as e:
        return f"Error: {str(e)}"
