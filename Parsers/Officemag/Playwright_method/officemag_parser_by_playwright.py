"""
Быстрое обновление остатков ОФИСМАГ
Скрипт считывает номер каталога, прогружает все его страницы и собирает: артикул, url, название, остатки.
"""
import pickle
from bs4 import BeautifulSoup
import re
import os
import json
import traceback
import requests
import datetime
import time
from tqdm import tqdm
from pathlib import Path
import pandas as pd

from playwright.sync_api import Playwright, sync_playwright, expect


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def my_decorator(func):
    def wrapper():
        # print('-------------действия перед вызовом функции------------')
        t1 = datetime.datetime.now()
        print(f'Start: {t1}')
        try:
            func()
        except Exception as exp:
            print(exp)
            # self.send_logs_to_telegram(message=f'Произошла ошибка!\n\n\n{exp}')
        # print('-------------действия после вызовом функции------------')
        t2 = datetime.datetime.now()
        print(f'Finish: {t2}, TIME: {t2 - t1}')
        # self.send_logs_to_telegram(message=f'Finish: {t2}, TIME: {t2 - t1}')

    return wrapper


def clear_price(price):
    """Очищаем цену от посторонних запахов и приводим к типу int"""
    if ',' in price:
        price = price.split(',')[0].replace(u'\xa0', '')
        return price
    else:
        price = price.replace(u'\xa0', '')
        return price


def clear_text(text_for_clear):
    if text_for_clear == 0:
        return 0
    """Очищаем текст от шт, точек, пробелов, плюсов и пр."""
    text_for_clear = text_for_clear.replace('шт.', '').replace(' ', '').replace(u'\xa0', '').replace('+', '')
    return text_for_clear


class ParserOfficeMag:
    def __init__(self):
        self.result_data = []
        self.links = []  # ссылки на товары, полученные из ссылок на каталоги
        self.stocks = []
        self.stocks_krasnoarmeyskaya = []
        self.stocks_sovetskaya = []
        self.page = None
        self.context = None
        self.browser = None
        self.__main_url = 'https://www.officemag.ru/'
        self.remove_from_description = ['в нашем интернет-магазине', 'у нас на сайте']
        self.df_ozon = pd.DataFrame()
        self.df_ozon_bad_brend = pd.DataFrame()
        self.df_wb = pd.DataFrame()
        self.df_wb_bad_brend = pd.DataFrame()

        self.product_name = []  # Название товара
        self.brand = []
        self.description_list = []  # описание
        self.features_colour_list = []  # цвет
        self.features_package_weight_list = []  # вес в упаковке
        self.features_package_length_list = []  # Длина упаковки
        self.features_packing_width_list = []  # ширина в упаковке
        self.features_packing_height_list = []  # Высота упаковки
        self.features_manufacturer_list = []  # Производитель
        self.url_main_img_add_list = []  # основное фото товара
        self.url_img_add_list = []  # дополнительные ссылки на товар из карточки
        self.video_lst = []  # видео товара
        self.price_discount_list = []  # цена с учетом скидки
        self.krasnoarmeyskaya_list = []
        self.sovetskaya_list = []

        self.js = """
        Object.defineProperties(navigator, {webdriver:{get:()=>undefined}});
        """

    def read_bad_brand_from_txt(self):
        with open('bad_brand.txt', 'r', encoding='utf-8') as file:
            bad_brand = [f'{line}'.rstrip() for line in file]
            return bad_brand

    def read_login_from_txt(self):
        with open(f'{current_directory}\\login.txt', 'r', encoding='utf-8') as file:
            rows = [f'{line}'.rstrip() for line in file]
            return rows

    def read_abc_catalogs(self):
        with open(f'{current_directory}\\abc_catalogs.txt', 'r', encoding='utf-8') as file:
            rows = [f'{line}'.rstrip() for line in file]
            return rows

    def login(self):
        print(f'{bcolors.OKGREEN}login{bcolors.ENDC}')
        # self.page.set_viewport_size({"width": 1000, "height": 800})
        # self.page.goto(self.__main_url)
        self.page.goto('https://www.officemag.ru/auth/')
        login = self.read_login_from_txt()[0]
        my_pass = self.read_login_from_txt()[1]
        time.sleep(1)
        self.page.keyboard.press("Escape")
        time.sleep(1)
        # self.page.get_by_text("Вход").click()
        # Находим поле ввода по его id
        input_login = self.page.locator('#USER_LOGIN')
        # Вводим текст в поле ввода
        input_login.fill(login)
        # Находим поле ввода USER_PASSWORD по его id
        input_pass = self.page.locator('#USER_PASSWORD')
        # Вводим пароль в поле ввода
        input_pass.fill(my_pass)
        # Находим кнопку Login и клик
        login_button = self.page.locator('[name="Login"]')
        login_button.click()
        time.sleep(1)

    def get_abc_catalog(self):
        self.page.goto('https://www.officemag.ru/catalog/abc/')
        abc = self.page.locator('.catalogAlphabetList threeColumns')

    def get_articles_by_catalog(self, abc_catalogs):
        "Находим все ссылки на артикулы из каталога и обновляем остатки, т.к. они есть на странице каталога"
        for c_number in tqdm(abc_catalogs):
            print(f'{bcolors.OKGREEN}Номер каталога: {c_number}{bcolors.ENDC}')
            page_number = 1
            while True:
                print(f'{bcolors.BOLD}Номер страницы: {page_number}{bcolors.ENDC}')
                self.page.goto(f'https://www.officemag.ru/catalog/{c_number}/?SORT=SORT&COUNT=60&PAGEN_1={page_number}')
                self.page.wait_for_load_state('load')
                # Получаем текст на странице
                page_text = self.page.inner_text('body')
                if "Товары не найдены" in page_text:
                    print(f'{bcolors.WARNING}Товары не найдены{bcolors.ENDC}')
                    break
                else:
                    "Получим HTML-код страницы для приготовления супа"
                    page_content = self.page.content()
                    # Используем BeautifulSoup для парсинга HTML
                    soup = BeautifulSoup(page_content, 'html.parser')
                    "Найдем блок, содержащий элементы товаров"
                    list_items = soup.find_all('div', class_='listItem__content')

                    for content_item in list_items:
                        "Найдем код (артикул) товара"
                        code = content_item.find('span', class_='code').text.replace('Код ', '')
                        # Найдем статус товара (в наличии, Выведен из ассортимента и т.д.)
                        product_status = content_item.find('div', class_='listItemBuy__available').contents[1].attrs[
                            'class']
                        if 'ProductState--assortmentRemoved' in product_status:
                            print(f'{bcolors.WARNING}Товар {code} выведен из ассортимента{bcolors.ENDC}')
                            break
                        if 'ProductState--outStock' in product_status:
                            print(f'{bcolors.WARNING}Товар {code} временно отсутствует на складе{bcolors.ENDC}')
                            break
                        if 'ProductState--green' in product_status:
                            # print('ProductState--green')

                            # "Найдем код (артикул) товара"
                            # code = content_item.find('span', class_='code').text.replace('Код ', '')
                            # if code == '630680':
                            #     print()
                            print(f'code = {code}')

                            "Найдем название товара"
                            name = content_item.find('div', class_='name').text.strip()

                            "Найдем url товара"
                            url = content_item.find('div', class_='name').contents[1].attrs['href']

                            "Найдем цену товара"
                            # Специальная цена (если цена указана от нескольких штук, то уходим внутрь и достаем цену
                            # за 1 шт.)
                            price_best = content_item.find('span', class_='Price Price--best')
                            price_ = content_item.find('span', class_='Price')
                            special_price = content_item.find('div', class_='ProductSpecial js-productSpecial')
                            if price_best and special_price is None:
                                price = price_best.text
                                price = clear_price(price)
                            elif special_price:
                                price = special_price.find('span', class_='Price__count').text
                                price = clear_price(price)
                            elif price_best is None and price_:
                                price = price_.text
                                price = clear_price(price)
                            else:
                                print(f'{bcolors.FAIL}непонятки с ценой ({code}) {bcolors.ENDC}')

                            "Найдем остатки товара"
                            stocks = content_item.find('span', class_='pseudoLink')
                            if 'data-content-replace' in stocks.attrs:  # товар есть, или нет, но он доступен к заказу
                                # Извлекаем значение атрибута data-content-replace
                                stocks_data_content = stocks.attrs['data-content-replace']
                                # Парсим JSON
                                stocks_data_content_dict = json.loads(stocks_data_content)
                                # Проверяем статус остатков на Красноармейской (omr_20C)
                                if stocks_data_content_dict['omr_20C'] == 'green':
                                    stocks_krasnoarmeiskaya = int(clear_text(stocks_data_content_dict['omr_20T']))
                                else:
                                    stocks_krasnoarmeiskaya = 0
                                # Проверяем статус остатков на Советской (omr_102C)
                                if stocks_data_content_dict['omr_102C'] == 'green':
                                    stocks_sovetskaya = int(clear_text(stocks_data_content_dict['omr_102T']))
                                else:
                                    stocks_sovetskaya = 0
                                # Проверяем статус остатков на удаленном складе (svhC)
                                if 'svhC' in stocks_data_content_dict and stocks_data_content_dict['svhC'] == 'green':
                                    stocks_remote_warehouse = int(clear_text(stocks_data_content_dict['svhT']))
                                else:
                                    stocks_remote_warehouse = 0
                            else:  # товара нет и он недоступен к заказу
                                # print(f'товара {code} нет и он недоступен к заказу, но может быть на складе')
                                stocks_krasnoarmeiskaya = stocks_sovetskaya = stocks_remote_warehouse = 0
                            try:
                                # Проверяем статус остатков в наличии на складе
                                pt = (content_item.find('div', class_='listItemBuy__available')
                                      .find('table', class_='AvailabilityList')
                                      .find_all('td', class_='AvailabilityBox'))
                                if len(pt) == 2:
                                    stocks_warehouse = pt[1].text if 'Наличие на складе' in pt[0].text else 0
                                    stocks_warehouse = int(clear_text(stocks_warehouse))
                                    stocks_remote_warehouse = pt[1].text if 'Под заказ' in pt[0].text else 0
                                    stocks_remote_warehouse = int(clear_text(stocks_remote_warehouse))
                                if len(pt) == 4:
                                    stocks_warehouse = pt[1].text if 'Наличие на складе' in pt[0].text else 0
                                    stocks_warehouse = int(clear_text(stocks_warehouse))
                                    stocks_remote_warehouse = pt[3].text if 'Под заказ' in pt[2].text else 0
                                    stocks_remote_warehouse = int(clear_text(stocks_remote_warehouse))
                            except Exception as exp:
                                print(f'{bcolors.WARNING}Случай, когда товара ({code}) нет ни на складе в Брянск, ни на'
                                      f' удаленном складе{bcolors.ENDC} \n\n'
                                      f'Ошибка: \n\n{exp}\n')
                                stocks_warehouse = stocks_remote_warehouse = 0
                        res_content_item_dict = {'Артикул': f'goods_{code}', 'Название': name,
                                                 'Цена в магазине': int(price),
                                                 'Цена для продажи': round(int(price) * 3.3),
                                                 'Сумма остатков на Красноармейской и Советской': int(
                                                     stocks_krasnoarmeiskaya) + int(stocks_sovetskaya),
                                                 'Остатки на Красноармейской': stocks_krasnoarmeiskaya,
                                                 'Остатки на Советской': stocks_sovetskaya,
                                                 'Остатки на складе в Брянске': stocks_warehouse,
                                                 'Под заказ': stocks_remote_warehouse,
                                                 'url': f'https://www.officemag.ru{url}'
                                                 }
                        self.result_data.append(res_content_item_dict)
                        pickle.dump(self.result_data, open('result_data.sav', 'wb'))
                        # print()
                    # create_xls_by_dict(self.result_data)
                    page_number += 1

    def create_xls(self, df):
        """Создание файла excel из 1-го DataFrame"""
        abc_catalogs = self.read_abc_catalogs()
        file_name = f'OM_Stocks_{abc_catalogs[0]}_{abc_catalogs[-1]}.xlsx'
        writer = pd.ExcelWriter(file_name, engine_kwargs={'options': {'strings_to_urls': False}})
        df.to_excel(writer, sheet_name='Остатки Офисмаг', index=False, na_rep='NaN', engine='openpyxl')
        # Auto-adjust columns'
        for column in df:
            column_width = max(df[column].astype(str).map(len).max(), len(column)) + 2
            col_idx = df.columns.get_loc(column)
            writer.sheets[f'{"Остатки Офисмаг"}'].set_column(col_idx, col_idx, column_width)
        # writer.sheets["OZON"].set_column(1, 1, 30)
        writer.close()
        print(f'{bcolors.OKGREEN}Успешно создан файл: {file_name}{bcolors.ENDC}')

    def send_logs_to_telegram(self, message):
        import platform
        import socket
        import os

        platform = platform.system()
        hostname = socket.gethostname()
        user = os.getlogin()

        bot_token = '6456958617:AAF8thQveHkyLLtWtD02Rq1UqYuhfT4LoTc'
        chat_id = '128592002'

        url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
        data = {"chat_id": chat_id, "text": message + f'\n\n{platform}\n{hostname}\n{user}'}
        response = requests.post(url, data=data)
        return response.json()

    def start(self):
        t1 = datetime.datetime.now()
        print(f'Start: {t1}')
        try:
            with sync_playwright() as playwright:
                self.browser = playwright.chromium.launch(headless=False, args=['--blink-settings=imagesEnabled=false'])
                self.context = self.browser.new_context()
                # self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
                self.page = self.context.new_page()
                self.page.add_init_script(self.js)
                self.login()
                abc_catalogs = self.read_abc_catalogs()
                self.get_articles_by_catalog(abc_catalogs=abc_catalogs)
                # self.context.tracing.stop(path="trace.zip")
                df = pd.DataFrame(self.result_data)
                self.create_xls(df)
                # self.get_abc_catalog()
                print()
        except Exception as exp:
            print(exp)
            # Получить информацию о стеке вызовов
            traceback_info = traceback.format_exc()
            print("Информация о стеке вызовов:\n\n", traceback_info)
            self.send_logs_to_telegram(message=f'Произошла ошибка!\n\n\n{exp}')
        t2 = datetime.datetime.now()
        print(f'Finish: {t2}, TIME: {t2 - t1}')
        self.send_logs_to_telegram(message=f'Finish: {t2}, TIME: {t2 - t1}')


if __name__ == '__main__':
    current_directory = os.path.dirname(__file__) if '__file__' in locals() else os.getcwd()
    ParserOfficeMag().start()
