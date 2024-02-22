import requests

def get_free_proxies():
    url = 'https://api.getproxylist.com/proxy'
    response = requests.get(url)
    data = response.json()
    if 'ip' in data and 'port' in data:
        proxy = f"{data['protocol']}://{data['ip']}:{data['port']}"
        return proxy
    else:
        return None

if __name__ == "__main__":
    proxy = get_free_proxies()
    if proxy:
        print(f"Следующий бесплатный прокси: {proxy}")
    else:
        print("Не удалось получить бесплатный прокси.")
