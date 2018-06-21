#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
 Проект:            	Мониторинг общественного мнения
 Автор:             	Булдей Александр
 Связь :                https://t.me/Alex_Booldey
 Описание :             Скрипт сбора информации из википедии

 Версия :           	1.0
"""
import re
import sys
import requests

from time import sleep
from bs4 import BeautifulSoup
from urllib.parse import unquote
from urllib.parse import urlparse

import utils
from utils import log

time_flag = False
count_failed_pages = 0


class WikiCrawler:

    # Функция инициализации кравлера, вызываеться автоматически при создании класса;
    def __init__(self):
        log.info("Initialization сrawler...")
        # Чтение конфиг файла
        self.conf = utils.load_config()
        self.queue = []

        self.session = requests.session()

        self.user_agent = self.conf["crawler"]["user_agent"]

        self.parenthesis_regex = re.compile('\(.+?\)')
        self.citations_regex = re.compile('\[.+?\]')

        # Инициализация класса для форматирования даты
        self.formatter = utils.DateFormatter()

        # Инифиализация соединения с базой данных
        self.db = utils.DatabaseConnection(self.conf)
        log.info("Initialization end!")

    # Функция загрузки страници
    # in - url страници
    # out - html страници
    @utils.time_util(time_flag)
    def load_page(self, full_url, level=0, sleep_time=10):
        global count_failed_pages

        try:
            page = self.session.get(full_url, allow_redirects=True, timeout=20,
                                    headers={'User-Agent': self.user_agent})
        except requests.exceptions.ConnectionError:
            log.error("Check your Internet connection")

            if level in range(0, 5):
                sleep(sleep_time)
            elif level in range(5, 10):
                sleep(sleep_time * 180)
            elif level > 10:
                if count_failed_pages >= 5:
                    log.critical("Wikipedia exit 0, Check your Internet connection")
                    sys.exit(0)

                count_failed_pages += 1
                return

            return self.load_page(full_url, level + 1)

        if page.status_code not in (200, 404):
            log.error("Failed to request page (code {})".format(page.status_code))
            return
        return page

    # Функция извлечения основного текста со станици
    # in - html страници
    # out - текст
    @utils.time_util(time_flag)
    def get_content(self, soup):
        content = ""
        try:
            div = soup.find('div', {'id': 'mw-content-text'})
            p_list = div.find_all('p')

            for p in p_list:
                try:
                    text = p.get_text().strip()
                except Exception as e:
                    log.error(e)
                    continue

                text = self.parenthesis_regex.sub('', text)
                text = self.citations_regex.sub('', text)

                if not content.strip():
                    content = text + '\n'
                else:
                    content = content + " " + text + '\n'
            return content
        except Exception as e:
            log.error(e)

    # Функция извлечения категорий со страницы
    # in soup - html по которому ведется поиск
    # out - list категорий
    @staticmethod
    @utils.time_util(time_flag)
    def get_categories(soup):
        categories = []

        try:
            div_categories = soup.find("div", {'id': 'mw-normal-catlinks'}).find("ul")
            a_list = div_categories.find_all("a")
            for category in a_list:
                try:
                    parts = category.get("title").rsplit(':', 1)
                    categories.append(parts[1])
                except Exception as e:
                    log.error(e)
                    continue
        except Exception as e:
            log.error(e)

        return categories

    # Функция извлечения истории изменения страницы
    # in - ulr статьи
    # out - list[0] - дата/время изменения
    #       list[1] - автор
    @utils.time_util(time_flag)
    def get_history(self, article_url, lang):
        history = []
        pages = []

        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(article_url))
        url_history = "https://{0}.wikipedia.org/w/index.php?title={1}&offset=&limit=500&action=history" \
            .format(lang, unquote(article_url[len(base_url + '/wiki/'):]))

        response = self.load_page(url_history)
        if response is None:
            return
        soup = BeautifulSoup(response.text, 'html.parser')

        while True:
            if not len(pages) == 0:
                response = self.load_page(pages.pop(0))
                if response is None:
                    return
                soup = BeautifulSoup(response.text, 'html.parser')

            try:
                ul_history = soup.find("ul", {'id': 'pagehistory'})
                li_list = ul_history.find_all("li")
                for element in li_list:
                    try:
                        user = element.find("bdi").text

                        wiki_date = element.find("a", {'class': 'mw-changeslist-date'}).text
                        if lang in self.formatter.lang_support_default:
                            sql_date = self.formatter.convert_date(lang, wiki_date)
                            history.append((sql_date, user))
                        else:
                            history.append((None, user, wiki_date))
                    except Exception as e:
                        log.error(e)
                        continue
            except Exception as e:
                log.error(e)

            try:
                next_url = soup.find("a", {'rel': 'next'})['href']
                if next_url:
                    next_url = base_url + next_url
                    pages.append(next_url)
            except Exception as e:
                log.debug(e)
                break
        return history

    @utils.time_util(time_flag)
    def get_lang(self, soup):
        div_lang = soup.find("div", {'id': 'p-lang'})
        li_list = div_lang.find_all("li")

        for li in li_list:
            a = li.find('a', href=True)
            self.queue.append(a['href'])

    @utils.time_util(time_flag)
    def scrap(self, url):

        page = self.load_page(url)

        if page is None:
            return
        else:
            lang = utils.get_lang(url)
            page_url = unquote(page.url)
            page_url_hash = utils.get_hash(page_url)

            if (lang is None) or (self.db.is_exists(page_url_hash)):
                return

            soup = BeautifulSoup(page.text, 'html.parser')

            content = self.get_content(soup)
            categories = self.get_categories(soup)
            history = self.get_history(page_url, lang)

            if history:
                created_data = history[len(history) - 1][0]
                created_user = history[len(history) - 1][1]
            else:
                created_user = None
                created_data = None

            processed_article = [soup.h1.text, page_url, created_user, created_data, content, lang, page_url_hash]
            last_id = self.db.save_article(processed_article)

            if categories:
                self.db.save_categories(last_id, categories)
            if history:
                self.db.save_history(last_id, history)

            if lang == "ru":
                self.get_lang(soup)

    def start(self):
        initial_url = "https://ru.wikipedia.org/wiki/Special:Random"
        self.queue.append(initial_url)

        while len(self.queue) > 0:
            try:
                next_url = self.queue.pop(0)
            except IndexError:
                break

            self.scrap(next_url)

            if len(self.queue) == 0:
                self.queue.append(initial_url)
        sys.exit(0)


if __name__ == '__main__':
    WikiCrawler().start()
