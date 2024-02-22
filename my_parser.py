import time
import json
import os
import pprint
import sqlite3
import random
import requests
import asyncio
import itertools
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from seleniumwire import webdriver
from datetime import datetime, timezone, timedelta

CONFIG_FILE = "config.json"
API_KEY = "10d965f4b8-d3ef156b2e-c460b4342d"
BASE_URL = "https://proxy6.net/api"

proxies = []
# proxy_index = 0;
links = []

proxy_index = 0

user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4700.72 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4713.93 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4721.106 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4732.99 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.4740.123 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.4751.158 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.4763.201 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.4778.322 Safari/537.36"
]

async def get_next_proxy(proxies, current_proxy):
    if current_proxy is None:
        return None  # Если текущий прокси не определен, вернем None
    try:
        index = proxies.index(current_proxy)
        next_index = (index + 1) % len(proxies)  # Переходим к следующему прокси в списке по кругу
        return proxies[next_index]
    except ValueError:
        return None  # Если текущий прокси не найден в списке, вернем None

def get_proxy():
    try:
        url = f"{BASE_URL}/{API_KEY}/getproxy/?state=active&limit=5"
        response = requests.get(url)
        if response.status_code == 200:
            proxy_data = response.json()
            return proxy_data
        else:
            print("Failed to get proxies from Proxy6 API.")
            return []
    except Exception as e:
        print("An error occurred while getting proxies:", e)
        return []

def buy_proxy(count, period, country, type):
    try:
        url = f"{BASE_URL}/{API_KEY}/buy?count={count}&period={period}&country={country}&type={type}"
        response = requests.get(url)
        if response.status_code == 200:
            proxy_data = response.json()
            if 'list' in proxy_data:
                proxies = [f"{proxy['host']}:{proxy['port']}" for proxy in proxy_data['list'].values()]
                return proxies
            else:
                print("Failed to buy proxies from Proxy6 API.")
                return []
        else:
            print("Failed to buy proxies from Proxy6 API.")
            return []
    except Exception as e:
        print("An error occurred while purchasing proxies:", e)
        return []

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    else:
        return {"notifications": "0"}
    
def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

async def scroll_to_bottom(driver):
    try:
        # Итерируемся по нескольким скроллам
        for scroll_percentage in [0.25, 0.5, 0.75, 1.0]:
            # Выполняем скроллинг к указанному проценту высоты страницы
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_percentage});")
            # Ждем случайное время перед следующим скроллом
            await asyncio.sleep(random.uniform(1, 5))
        
        # Проверяем, достигнут ли конец страницы после всех скролов
        current_scroll_position = driver.execute_script("return window.pageYOffset;")
        page_height = driver.execute_script("return document.body.scrollHeight;")
        if current_scroll_position < page_height:
            # Если не находимся внизу страницы, явно перемещаемся вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception as e:
        print("An error occurred while scrolling:", e)

async def generate_notifications(new_products_ids):
    try:
        conn = sqlite3.connect('yadb.db')
        cursor = conn.cursor()
        
        for product_id in new_products_ids:
            cursor.execute('''INSERT INTO NOTIFICATIONS (product_id, status) VALUES (?, ?)''', (product_id, 'new'))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print("An error occurred while generating notifications:", e)

async def parse_and_save_products(driver, url):
    global config
    try:
        products_data = []
        new_products_ids = []
        conn = sqlite3.connect('yadb.db')
        cursor = conn.cursor()
        
        articles = driver.find_elements(By.CSS_SELECTOR, 'article[data-autotest-id="offer-snippet"], article[data-autotest-id="product-snippet"]')
        
        for article in articles:
            
            zone_data_str = article.get_attribute("data-zone-data")
            zone_data = json.loads(zone_data_str)

            product_data = {
                "product_name": article.find_element(By.CSS_SELECTOR, 'h3[data-auto="snippet-title-header"] span').text,
                "min_price": int(zone_data.get("minPrice", 0)),
                "min_price_discount": 0,
                "discount": 0,
                "promocode": None,
                "promocode_discount": 0,
                "3eq2": False,
                "4eq3": False,
                "5eq4": False,
                "ya_bank_pay_price": int(zone_data.get("yaBankPrice", 0)),
                "max_discount": 0
            }
            print("0)", product_data["ya_bank_pay_price"])
            additional_prices = zone_data.get("additionalPrices", [])
            for price in additional_prices:
                if price.get("priceType") == "withDiscount" and product_data["min_price"] == 0:
                    product_data["min_price"] = price.get("priceValue")
                if price.get("priceType") == "yaBank" and product_data["ya_bank_pay_price"] == 0:
                    product_data["ya_bank_pay_price"] = price.get("priceValue")
                    break

            promos = zone_data.get("promos", [])
            for promo in promos:
                if promo.get("type") == "direct-discount":
                    product_data["discount"] = promo.get("value")
                elif promo.get("type") == "promo-code":
                    product_data["promocode"] = promo.get("promoCode")
                    product_data["promocode_discount"] = promo.get("value")
                elif promo.get("type") == "cheapest-as-gift":
                    landing_url = promo.get("landingUrl")
                    if "cheapest-as-gift-2-3" in landing_url:
                        product_data["3eq2"] = True
                    elif "cheapest-as-gift-3-4" in landing_url:
                        product_data["4eq3"] = True
                    elif "cheapest-as-gift-4-5" in landing_url:
                        product_data["5eq4"] = True

            print("1)", product_data["discount"])
            if product_data["discount"] == 0 and product_data["ya_bank_pay_price"] != 0: 
                # discount_amount = zone_data.get("price") - product_data["ya_bank_pay_price"]
                # discount_percentage = (discount_amount / zone_data.get("price")) * 100
                temp1 = zone_data.get("price") + product_data["ya_bank_pay_price"]
                temp2 = zone_data.get("price") - product_data["ya_bank_pay_price"]

                temp3 = temp1 / 2

                temp4 = temp2 / temp3

                product_data["discount"] = temp4 * 100
                pass
            print("name", product_data["product_name"])
            print("price", zone_data.get("price"))
            print("ybank", product_data["ya_bank_pay_price"])
            print("2)", product_data["discount"])
            print("---------------------------")

            # Получаем текущую дату и время по Москве
            now = datetime.now(timezone(timedelta(hours=3)))
            formatted_datetime = now.strftime("%Y-%m-%d %H:%M:%S.%f")

             # Получаем размер скидки для данной ссылки из таблицы LINKS
            cursor.execute('''SELECT discount FROM LINKS WHERE link = ?''', (url,))
            link_discount = cursor.fetchone()
            if link_discount:
                link_discount = link_discount[0]

            # Проверяем, удовлетворяет ли товар скидке для данной ссылки
            if product_data["discount"] >= 10:
                # Проверяем, существует ли товар в базе данных
                cursor.execute('''SELECT * FROM PRODUCTS WHERE 
                                product_name = ? AND
                                min_price = ? AND
                                discount = ? AND
                                ya_bank_pay_price = ?''',
                            (product_data['product_name'], product_data['min_price'],
                                product_data['discount'], product_data['ya_bank_pay_price']))
                existing_product = cursor.fetchone()

                # Если товара нет в базе данных, добавляем его
                if existing_product is None:
                    cursor.execute('''INSERT INTO PRODUCTS (
                                    product_name, min_price, min_price_discount, discount,
                                    promocode, promocode_discount, promo3eq2, promo4eq3,
                                    promo5eq4, ya_bank_pay_price, max_discount, datetime_added) VALUES (
                                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                                (product_data['product_name'], product_data['min_price'],
                                    product_data['min_price_discount'], product_data['discount'],
                                    product_data['promocode'], product_data['promocode_discount'],
                                    product_data['3eq2'], product_data['4eq3'], product_data['5eq4'],
                                    product_data['ya_bank_pay_price'], product_data['max_discount'],
                                    formatted_datetime))  # Добавляем дату и время
                    
                    new_products_ids.append(cursor.lastrowid)
                    conn.commit()

                products_data.append(product_data)
            
        # Закрываем соединение с базой данных
        conn.close()

        # Вызываем функцию для генерации уведомлений
        if config["notifications"] == "1":
            await generate_notifications(new_products_ids)

        return products_data
    except Exception as e:
        print(e)
    finally:
        pass
    
async def parser(url, proxy):
    user_agent = random.choice(user_agents)
    try:
        options = Options()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        # options.add_argument("--disable-extensions")
        # options.add_argument("--disable-infobars")
        # options.add_argument("--disable-breakpad")
        options.add_argument("--headless")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--v=99")
        options.add_argument("--no-sandbox")
        # options.add_argument('--disable-notifications')
        options.add_argument("--disable-blink-features=NetworkService")
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        # options.add_argument("--disable-update")
        options.add_argument("--disable-file-access-check")
        options.add_argument(f'--window-size={random.randint(800, 1200)},{random.randint(600, 1000)}')
        # options.add_argument('--proxy-server=socks5://A0ERht:dtEGMQ@217.29.63.40:11988')
        # options.add_argument('--proxy-auth=A0ERht:dtEGMQ')
        if proxy:
            options.add_argument(f'--proxy-server=socks5://{proxy["login"]}:{proxy["password"]}@{proxy["host"]}:{proxy["port"]}')
            options.add_argument(f'--proxy-auth={proxy["login"]}:{proxy["password"]}')
            # options.add_argument(f'--proxy-server=socks5://Lugv2e:K9yQ6K@217.29.63.159:11682')
            # options.add_argument(f'--proxy-auth=Lugv2e:K9yQ6K')
            print(f'--proxy-server=socks5://{proxy["login"]}:{proxy["password"]}@{proxy["host"]}:{proxy["port"]}')
        driver = webdriver.Chrome(options=options)
        driver.set_window_size(random.randint(800, 1200), random.randint(600, 1000))

        driver.get(url)
        # cookie = {'name': 'yandex_login', 'value': 'wind', 'domain': '.market.yandex.ru'}
        # driver.add_cookie(cookie)

        # driver.add_cookie({'name': 'sessionid2', 'value': '3:1708506798.5.0.1708506798056:iThruQ:17.1.2:1|893777999.-1.2.3:1708506798|3:10283429.157855.fakesign0000000000000000000'})
        # driver.add_cookie({'name': 'Session_id', 'value': '3:1708506798.5.0.1708506798056:iThruQ:17.1.2:1|893777999.-1.2.3:1708506798|3:10283429.157855.MLGyxT0KCN9mgM93gjUot4JgZdA'})
        # driver.add_cookie({'name': 'yandex_login', 'value': 'mirmicuper'})
        # driver.add_cookie({'name': 'spravka', 'value': 'dD0xNzA4NTAyOTU3O2k9MTg1LjEwNy41Ni4xMzc7RD0yMjY0QTc0NTNDMjIyRkNENjkzNUU0NTRDMTExQzAyREZCQzZDOEJENkU2QUQzRUExOEYxQjVGODlFRUI4MEU3NjY1OEUxREYwQjI1MDRCODE2MTZCQjYwMUY1Qjg1MkMwN0NBNzY3MkY5NTFCM0JEMEU4QzQ5QjhCREVEMTRCQUUxNUYzMzBEQkFGMjAxMDY3MkRFNkNCQUFBQjNFRTYyNTUyOEFCNTkwQTEzNENFM0VEQTA4OTBENTAyRTNFMDNCNzcyNzM3QzMxNTM7dT0xNzA4NTAyOTU3ODAwNDgyODYyO2g9NTQzYmUxZDcwOWRiZWUyNmRjZTM4NjI4OTQxMGI2Mjg='})
        # driver.add_cookie({'name': 'bh', 'value': 'EkEiTm90IEEoQnJhbmQiO3Y9Ijk5IiwgIkdvb2dsZSBDaHJvbWUiO3Y9IjEyMSIsICJDaHJvbWl1bSI7dj0iMTIxIhoFImFybSIiECIxMjEuMC42MTY3LjE2MCIqAj8wOgcibWFjT1MiQggiMTQuMS4xIkoEIjY0IlJcIk5vdCBBKEJyYW5kIjt2PSI5OS4wLjAuMCIsIkdvb2dsZSBDaHJvbWUiO3Y9IjEyMS4wLjYxNjcuMTYwIiwiQ2hyb21pdW0iO3Y9IjEyMS4wLjYxNjcuMTYwIiI='})
        # driver.add_cookie({'name': 'yandexuid', 'value': '7772393461707825395'})
        # driver.add_cookie({'name': 'ymex', 'value': '1740038602.yrts.1708502602'})
        # driver.add_cookie({'name': 'yuidss', 'value': '7772393461707825395'})
        # driver.add_cookie({'name': 'sessionid2', 'value': value})
        # driver.add_cookie({'name': 'sessionid2', 'value': value})
        # driver.implicitly_wait(40)
        # driver.refresh()

        driver.implicitly_wait(20)
        
        captcha_present = driver.find_elements(By.CLASS_NAME, 'CheckboxCaptcha-Anchor')
        if captcha_present:
            print("Капча обнаружена")
            checkbox = driver.find_element(By.CLASS_NAME, 'CheckboxCaptcha-Anchor')
            checkbox.click()
            time.sleep(random.uniform(5, 10))

        driver.implicitly_wait(random.uniform(10, 20))

        # Найдите элемент, для которого нужно изменить стиль курсора
        element = driver.find_element(By.ID, "header-search")     
        driver.execute_script("arguments[0].style.cursor = 'text';", element)  

        driver.implicitly_wait(20)
        # Добавить обработку капчи здесь, если необходимо

        await scroll_randomly(driver)

        products_data = await parse_and_save_products(driver, url)

        for product in products_data:
            print("Product Name:", product["product_name"])
            print("Min Price:", product["min_price"])
            print("Min Price with Discount:", product["min_price_discount"])
            print("Discount:", product["discount"])
            print("Promocode:", product["promocode"])
            print("Promocode Discount:", product["promocode_discount"])
            print("3eq2:", product["3eq2"])
            print("4eq3:", product["4eq3"])
            print("5eq4:", product["5eq4"])
            print("Yandex Bank Pay Price:", product["ya_bank_pay_price"])
            print()

    finally:
        driver.quit()

async def scroll_randomly(driver):
    try:
        for scroll_percentage in [0.25, 0.5, 0.75, 1.0]:
            # Генерируем случайный процент для скроллинга в указанном диапазоне
            scroll_percent = random.uniform(scroll_percentage - 0.15, scroll_percentage)
            # Выполняем скроллинг
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {scroll_percent});")
            # Генерируем случайную задержку перед следующим скроллингом
            await asyncio.sleep(random.uniform(1, 5))  # Пример случайной задержки от 1 до 5 секунд

        # Проверяем, достигнут ли конец страницы после всех скролов
        current_scroll_position = driver.execute_script("return window.pageYOffset;")
        page_height = driver.execute_script("return document.body.scrollHeight;")
        if current_scroll_position < page_height:
            # Если не находимся внизу страницы, явно перемещаемся вниз
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    except Exception as e:
        print("An error occurred while scrolling:", e)

def next_proxy_index():
    global proxy_index
    size_of_proxies = len(proxies)
    print("size index_proxy", size_of_proxies)
    print("index_proxy", proxy_index)
    if proxy_index >= size_of_proxies - 1:
        proxy_index = 0
    else:
        proxy_index = proxy_index + 1

async def main():
    global config
    global proxy_index
    config = load_config() 

    while True:
        proxy_data = get_proxy()

        for proxy_id, proxy_info in proxy_data["list"].items():
            proxy_obj = {
                "host": proxy_info["host"],
                "port": proxy_info["port"],
                "login": proxy_info["user"],
                "password": proxy_info["pass"]
            }
            proxies.append(proxy_obj)

        conn = sqlite3.connect('yadb.db')
        cursor = conn.cursor()
        cursor.execute("SELECT link FROM LINKS")
        rows = cursor.fetchall()
        links = [row[0] for row in rows]
        conn.close()

        print("1", proxies)
        
        if not proxies or len(proxies) < 3:
            print("Not enough proxies available. Buying more proxies...")
            proxy_data = buy_proxy(3 - len(proxies), 3, "ru", "socks")
            print("1-1", proxies)
            proxy_data = get_proxy()

            proxies.clear()
            print("1-2", proxies)
            for proxy_id, proxy_info in proxy_data["list"].items():
                proxy_obj = {
                    "host": proxy_info["host"],
                    "port": proxy_info["port"],
                    "login": proxy_info["user"],
                    "password": proxy_info["pass"]
                }
                proxies.append(proxy_obj)
            print("1-3", proxies)

        for link in links:
            try:
                print("2")
                proxy = proxies[proxy_index]
                next_proxy_index()
                await parser(link, proxy)
                print("Страница готова")
                print("-----------------------")

            except WebDriverException as e:
                print("3")
                if "net::ERR_CONNECTION_RESET" in str(e):
                    print("Connection reset error. Changing proxy...")
                elif "no such element" in str(e):
                    print('No such element. Unable to locate element.') 
                else:
                    print("An error occurred:", e)

                print("Не удалось подключиться")
                print("-----------------------")

            finally: 
                print("4")
                t = random.uniform(300, 500)
                print("Ожидание:", t)
                time.sleep(t)

        config["notifications"] = "1"
        save_config(config)

        # t = random.uniform(500, 700)
        # print("Глобальное ожидание:", t)
        # time.sleep(t)

if __name__ == "__main__":
    asyncio.run(main())
