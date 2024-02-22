from seleniumbase import BaseCase
import json
import random
import time

class MyTestClass(BaseCase):
    def test_yandex_market(self):
        self.open("https://market.yandex.ru/catalog--smartfony/26893750/list")
        self.wait_for_element_visible('article[data-autotest-id="offer-snippet"]', timeout=20)

        captcha_present = self.is_element_visible('.CheckboxCaptcha-Anchor')
        if captcha_present:
            print("Капча обнаружена")
            self.click('.CheckboxCaptcha-Anchor')
            time.sleep(random.uniform(5, 10))

        self.implicitly_wait(random.uniform(10, 20))

        self.scroll_to_bottom()

        articles = self.find_elements('article[data-autotest-id="offer-snippet"]')

        time.sleep(random.uniform(3, 5))

        products_data = []

        for article in articles:
            zone_data_str = article.get_attribute("data-zone-data")
            zone_data = json.loads(zone_data_str)

            product_data = {
                "id": zone_data.get("id"),
                "price": zone_data.get("price")
            }

            title_element = article.find_element('h3[data-auto="snippet-title-header"] span')
            product_data["title"] = title_element.text

            products_data.append(product_data)

        for product in products_data:
            print("ID:", product["id"])
            print("Title:", product["title"])
            print("Price:", product["price"], "Рублей")
            print()

def main():
    MyTestClass().test_yandex_market()

if __name__ == "__main__":
    main()
