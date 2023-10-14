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


class ParserOfficeMag:
    def __init__(self):
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
        with open('login.txt', 'r', encoding='utf-8') as file:
            login = [f'{line}'.rstrip() for line in file]
            return login

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
        inpit_pass = self.page.locator('#USER_PASSWORD')
        inpit_pass.fill(my_pass)
        login_button = self.page.locator('[name="Login"]')
        login_button.click()
        time.sleep(10)

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
        except Exception as exp:
            print(exp)
            # self.send_logs_to_telegram(message=f'Произошла ошибка!\n\n\n{exp}')
        t2 = datetime.datetime.now()
        print(f'Finish: {t2}, TIME: {t2 - t1}')
        # self.send_logs_to_telegram(message=f'Finish: {t2}, TIME: {t2 - t1}')


if __name__ == '__main__':
    ParserOfficeMag().start()
