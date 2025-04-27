from .tool_stock_price import get_stock_price
from .tool_system_uptime import get_system_uptime
from .tool_web_search import web_search

available_tool_implementations = [get_stock_price, get_system_uptime, web_search]

TOOL_IMPLEMENTATIONS_MAP = {
    "stock_price": get_stock_price,
    "system_uptime": get_system_uptime,
    "web_search": web_search,
}