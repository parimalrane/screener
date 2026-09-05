import requests

def get_tickers():
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    res = requests.get("https://api.nasdaq.com/api/screener/stocks?tableonly=true&limit=25&offset=0&download=true", headers=headers)
    data = res.json()
    print(data['data']['rows'][0])

if __name__ == "__main__":
    get_tickers()
