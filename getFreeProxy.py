import requests
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures

def download_proxy_list(url, filename):
    response = requests.get(url)
    if response.status_code == 200:
        with open(filename, 'wb') as f:
            f.write(response.content)
        print(f"Прокси-список успешно загружен и сохранен в файле: {filename}")
    else:
        print("Не удалось загрузить прокси-список.")
def check_proxy(proxy):
    proxies = {"http": proxy, "https": proxy}
    
    url = "http://example.com"  # Замените на ваш URL для проверки
    try:
        response = requests.get(url, proxies=proxies, timeout=1)
        if response.status_code == 200:
            print("check {proxy} is valid")
            return proxy
        else:
            print("check {proxy} is not valid")
    except:
        pass
    return None

def write_valid_proxies(valid_proxies, output_file):
    with open(output_file, 'w') as f:
        for proxy in valid_proxies:
            f.write(proxy + '\n')

if __name__ == "__main__":
    input_file = "http.txt"
    output_file = "valid_proxies.txt"
    chunk_size = 100
    
    with open(input_file, 'r') as f:
        proxies = [line.strip() for line in f]

    valid_proxies = []

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(check_proxy, proxy) for proxy in proxies]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                valid_proxies.append(result)

    write_valid_proxies(valid_proxies, output_file)
    print("Проверка завершена. Валидные прокси сохранены в файле:", output_file)
