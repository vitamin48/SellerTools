"""
Скрипт открывает файл Excel, полученный в результате парса. Забирает и группирует ссылки на изображения.
Загружает их в формате jpg с учетом требования OZON.
"""

import pandas as pd
import requests
from pathlib import Path

from playwright.sync_api import sync_playwright

from selenium import webdriver
from selenium.webdriver.chrome.service import Service

excel_file = r'C:\Users\Simon\PycharmProjects\pythonProject\Программы, скрипты\fixprice_parser-master\FP_5313137_5301065.xlsx'

df = pd.read_excel(excel_file)

articles = df['Артикул'].to_list()
main_photo_url = df['Ссылка на главное фото товара'].to_list()
other_photo_url = df['Ссылки на фото товара'].to_list()

o00 = other_photo_url[0].split(' ')

# new_other_photo_url = []
# for i in range(len(other_photo_url)):
#     new_other_photo_url.append(other_photo_url[i].split(' '))

now = [x.split(' ') for x in other_photo_url]
for i in range(len(main_photo_url)):
    now[i].insert(0, main_photo_url[i])

# response = requests.get(now[0][0])
# if response.status_code == 200:
#     save_path = f'{str(Path(__file__).parents[1])}\\Download_images\\{articles[0]}_1.jpg'
#     with open(save_path, 'wb') as file:
#         file.write(response.content)
#
#     print(f'Изображение {articles[0]} успешно сохранено')
# else:
#     print(f"Не удалось скачать изображение {articles[0]}. Статус:", response.status_code)

# driver = webdriver.Chrome(service=Service('chromedriver.exe'))
# driver.set_window_size(800, 800)
# driver.get('https://img.fix-price.com/800x800/_marketplace/images/origin/0e/0e3c086924a68ae2ca82b7336a376af1.jpg')
#
#
# driver.save_screenshot(f'__4.png')
# driver.quit()
#
# 'body > img'

js = """
 Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
 """

# image_url = 'https://img.fix-price.com/800x800/_marketplace/images/origin/0e/0e3c086924a68ae2ca82b7336a376af1.jpg'

# for url in now:
#     print(f'url = {url}')
#     for i in url:
#         print(f'i = {i}')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.add_init_script(js)
    page.set_viewport_size({"width": 800, "height": 800})
    for url in enumerate(now):
        for i in enumerate(url[1]):
            page.goto(i[1])
            file_path = f'download_images\\{articles[url[0]]}_{i[0] + 1}.jpg'
            page.screenshot(path=file_path)
            # print()

    browser.close()
