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
import time
import requests

from bs4 import BeautifulSoup
from urllib.parse import unquote
from urllib.parse import urlparse

import utils
from utils import log


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
    def load_page(self, full_url, sleep_time=10):
        count_retry = 1

        try:
            while not utils.is_connected():
                if count_retry in range(6):
                    log.error("NO INTERNET, Short retry [{0}/5], Next try -> {1} sec".format(count_retry, sleep_time))
                    time.sleep(sleep_time)
                elif count_retry in range(11):
                    long_sleep_time = sleep_time * 180
                    log.error(
                        "NO INTERNET, Long retry [{0}/5], Next try -> {1} sec".format(count_retry - 5, long_sleep_time))
                    time.sleep(long_sleep_time)
                elif count_retry > 10:
                    log.error("OOPS!! Error. Make sure you are connected to Internet and restart script.")
                    sys.exit(0)
                count_retry = count_retry + 1

            return self.session.get(full_url, allow_redirects=True, timeout=20, headers={'User-Agent': self.user_agent})

        except requests.ConnectionError as e:
            log.error("OOPS!! Connection Error. Technical Details given below.")
            log.error(e)
            return
        except requests.Timeout as e:
            log.error(str(e))
            return self.load_page(full_url)

    # Функция извлечения основного текста со станици
    # in - html страници
    # out - текст
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
    def get_history(self, article_url, lang):
        history = []
        pages = []

        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(article_url))

        history_page_url = "{0}/w/index.php?title={1}&offset=&limit=500&action=history".format(base_url, unquote(
            article_url[len(base_url + '/wiki/'):]))

        response_s = self.load_page(history_page_url)
        soup = BeautifulSoup(response_s.text, 'html.parser')

        while True:
            if pages:
                response = self.load_page(pages.pop(0))
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

    def get_page_in_other_languages(self, soup):
        div_lang = soup.find("div", {'id': 'p-lang'})
        li_list = div_lang.find_all("li")

        for li in li_list:
            a = li.find('a', href=True)
            self.queue.append(a['href'])

    def scrap(self, url):

        page = self.load_page(url)

        page_url = unquote(page.url)
        page_url_hash = utils.get_hash(page_url)

        if self.db.is_exists(page_url_hash):
            return

        soup = BeautifulSoup(page.text, 'html.parser')

        page_content = self.get_content(soup)
        page_categories = self.get_categories(soup)

        language_code = utils.get_language_code(url)
        page_history = self.get_history(page_url, language_code)

        if page_history:
            created_data = page_history[len(page_history) - 1][0]
            created_user = page_history[len(page_history) - 1][1]
        else:
            created_user = None
            created_data = None

        processed_article = [soup.h1.text, page_url, created_user, created_data, page_content, language_code,
                             page_url_hash]
        last_id = self.db.save_article(processed_article)

        if page_categories:
            self.db.save_categories(last_id, page_categories)
        if page_history:
            self.db.save_history(last_id, page_history)

        if language_code == "ru":
            self.get_page_in_other_languages(soup)

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
