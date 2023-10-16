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
    """Очищаем текст от шт, точек, пробелов, плюсов и пр."""
    text_for_clear = text_for_clear.replace('шт.', '').replace(' ', '').replace(u'\xa0', '').replace('+', '')
    return text_for_clear


class ParserOfficeMag:
    def __init__(self):
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
        self.page.goto(self.__main_url)
        login = self.read_login_from_txt()[0]
        my_pass = self.read_login_from_txt()[1]
        self.page.get_by_text("Вход").click()
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
        print()

    def get_articles_by_catalog(self, abc_catalogs):
        "Находим все ссылки на артикулы из каталога и обновляем остатки, т.к. они есть на странице каталога"
        for c_number in abc_catalogs:
            print(f'Номер каталога: {c_number}')
            page_number = 1
            while True:
                print(f'Номер страницы: {page_number}')
                self.page.goto(f'https://www.officemag.ru/catalog/{c_number}/?SORT=SORT&COUNT=60&PAGEN_1={page_number}')
                self.page.wait_for_load_state('load')
                # Получаем текст на странице
                page_text = self.page.inner_text('body')
                if "Товары не найдены" in page_text:
                    print("Товары не найдены")
                    break
                else:
                    "Получим HTML-код страницы для приготовления супа"
                    page_content = self.page.content()
                    # Используем BeautifulSoup для парсинга HTML
                    soup = BeautifulSoup(page_content, 'html.parser')
                    "Найдем блок, содержащий элементы товаров"
                    list_items = soup.find_all('div', class_='listItem__content')

                    for content_item in list_items:
                        # Найдем статус товара (в наличии, Выведен из ассортимента и т.д.)
                        product_status = content_item.find('div', class_='listItemBuy__available').contents[1].attrs[
                            'class']
                        if 'ProductState--assortmentRemoved' in product_status:
                            print(f'Товар выведен из ассортимента')
                            break
                        if 'ProductState--outStock' in product_status:
                            print('ProductState--outStock')
                            break
                        if 'ProductState--green' in product_status:
                            print('ProductState--green')

                            "Найдем код (артикул) товара"
                            code = content_item.find('span', class_='code').text.replace('Код ', '')
                            if code == '630680':
                                print()
                            print(f'code = {code}')

                            "Найдем название товара"
                            name = content_item.find('div', class_='name').text.strip()

                            "Найдем url товара"
                            url = content_item.find('div', class_='name').contents[1].attrs['href']
                            print()

                            "Найдем цену товара"
                            # Специальная цена (если цена указана от нескольких штук, то уходим внутрь и достаем цену
                            # за 1 шт.)
                            special_price = content_item.find('div', class_='ProductSpecial js-productSpecial')
                            if special_price:
                                price = special_price.find('span', class_='Price__count').text
                                price = clear_price(price)
                            else:
                                price = content_item.find('span', class_='Price Price--best').text
                                price = clear_price(price)
                            print()

                            "Найдем остатки товара"
                            stocks = content_item.find('span', class_='pseudoLink')
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
                            if stocks_data_content_dict['svhC'] == 'green':
                                stocks_remote_warehouse = int(clear_text(stocks_data_content_dict['svhT']))
                            else:
                                stocks_remote_warehouse = 0
                            print()

                    # # Находим все элементы с классом "name", чтобы извлечь ссылки в дальнейшем
                    # elements = self.page.query_selector_all('.name')
                    # for element in elements:
                    #     link = element.query_selector('a')
                    #     if link:
                    #         href = link.get_attribute('href')
                    #         self.links.append(href)
                    #

                    page_number += 1

    def start(self):
        t1 = datetime.datetime.now()
        print(f'Start: {t1}')
        try:
            with sync_playwright() as playwright:
                self.browser = playwright.chromium.launch(headless=False, args=['--blink-settings=imagesEnabled=false'])
                self.context = self.browser.new_context()
                self.page = self.context.new_page()
                self.page.add_init_script(self.js)
                self.login()
                abc_catalogs = self.read_abc_catalogs()
                self.get_articles_by_catalog(abc_catalogs=abc_catalogs)
                # self.get_abc_catalog()
                print()
        except Exception as exp:
            print(exp)
            # Получить информацию о стеке вызовов
            traceback_info = traceback.format_exc()
            print("Информация о стеке вызовов:\n\n", traceback_info)
            # self.send_logs_to_telegram(message=f'Произошла ошибка!\n\n\n{exp}')
        t2 = datetime.datetime.now()
        print(f'Finish: {t2}, TIME: {t2 - t1}')
        # self.send_logs_to_telegram(message=f'Finish: {t2}, TIME: {t2 - t1}')


if __name__ == '__main__':
    current_directory = os.path.dirname(__file__) if '__file__' in locals() else os.getcwd()
    ParserOfficeMag().start()
