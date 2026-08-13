"""Fetch live crypto market data from CoinGecko."""
import requests

def get_top_cryptos(limit: int = 10) -> list[dict]:
    """Get top cryptocurrencies by market cap."""
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": limit,
        "page": 1,
        "sparkline": "false"
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return [
                {
                    "name": coin["name"],
                    "symbol": coin["symbol"].upper(),
                    "price_usd": coin.get("current_price"),
                    "market_cap_rank": coin.get("market_cap_rank"),
                    "price_change_24h": coin.get("price_change_percentage_24h")
                }
                for coin in data
            ]
    except Exception as e:
        print(f"Error fetching market data: {e}")
    
    return []

def get_market_summary() -> str:
    """Get market summary as text."""
    top = get_top_cryptos(10)
    if not top:
        return ""
    
    summary = "Current Top Cryptocurrencies by Market Cap:\n"
    for i, coin in enumerate(top, 1):
        change = coin.get("price_change_24h")
        change_str = f"{change:+.2f}%" if change is not None else "N/A"
        summary += f"{i}. {coin['name']} ({coin['symbol']}): ${coin.get('price_usd', 0):,.2f} ({change_str} 24h)\n"
    
    return summary
