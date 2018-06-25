#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = "Alex Booldey"
__project__ = "Mind Cloud"

__license__ = 'MIT'
__version__ = '1.0'
__maintainer__ = "Alex Booldey"
__contact__ = "https://t.me/Alex_Booldey"
__status__ = 'Development'

import re
import sys
import time
import utils
import requests

from utils import log
from bs4 import BeautifulSoup
from urllib.parse import unquote
from urllib.parse import urlparse


class WikiCrawler:

    def __init__(self):
        log.info("Initialization сrawler...")

        self.conf = utils.load_config()
        self.queue = []

        self.session = requests.session()
        self.user_agent = self.conf["crawler"]["user_agent"]

        self.parenthesis_regex = re.compile('\(.+?\)')
        self.citations_regex = re.compile('\[.+?\]')

        self.formatter = utils.DateFormatter()
        self.db = utils.DatabaseConnection(self.conf)

        log.info("Initialization end!")

    # out - html page
    def load_page_by_url(self, full_url, sleep_time=10):
        count_retry = 1

        try:
            while not utils.is_connected():
                if count_retry in range(6):
                    log.warn("NO INTERNET, Short retry [{0}/5], Next try -> {1} sec".format(count_retry, sleep_time))
                    time.sleep(sleep_time)
                elif count_retry in range(11):
                    long_sleep_time = sleep_time * 180
                    log.warn(
                        "NO INTERNET, Long retry [{0}/5], Next try -> {1} sec".format(count_retry - 5, long_sleep_time))
                    time.sleep(long_sleep_time)
                elif count_retry > 10:
                    log.critical("OOPS!! Error. Make sure you are connected to Internet and restart script.")
                    sys.exit(0)
                count_retry = count_retry + 1

            return self.session.get(full_url, allow_redirects=True, timeout=20, headers={'User-Agent': self.user_agent})

        except requests.ConnectionError as e:
            log.warn(e)
            return
        except requests.Timeout as e:
            log.warn(e)
            return self.load_page_by_url(full_url)

    # Function of extracting the main text from the page
    # in  - html page
    # out - text from page
    def get_content(self, soup):
        content = ""
        try:
            div = soup.find('div', {'id': 'mw-content-text'})
            p_list = div.find_all('p')

            for p in p_list:
                try:
                    text = p.get_text().strip()
                except AttributeError:
                    continue

                text = self.parenthesis_regex.sub('', text)
                text = self.citations_regex.sub('', text)

                if not content.strip():
                    content = text + '\n'
                else:
                    content = content + " " + text + '\n'
            return content
        except AttributeError as e:
            log.warn(e)

    # Function of extracting categories from the page
    # in  - html page
    # out - list get_category
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
                except AttributeError as e:
                    log.error(e)
                    continue
        except AttributeError:
            pass
        return categories

    # Function of extracting the history of the page change
    # in  - article url
    # out - list[0] - date / time of change
    #       list[1] - author
    def get_history(self, article_url, lang):
        history = []
        pages = []

        base_url = '{uri.scheme}://{uri.netloc}'.format(uri=urlparse(article_url))

        history_page_url = "{0}/w/index.php?title={1}&offset=&limit=500&action=history".format(base_url, unquote(
            article_url[len(base_url + '/wiki/'):]))

        response_s = self.load_page_by_url(history_page_url)
        if not response_s:
            return

        soup = BeautifulSoup(response_s.text, 'html.parser')

        while True:
            if pages:
                response = self.load_page_by_url(pages.pop(0))
                if not response:
                    return

                soup = BeautifulSoup(response.text, 'html.parser')

            try:
                ul_history = soup.find("ul", {'id': 'pagehistory'})
                li_list = ul_history.find_all("li")
                for element in li_list:
                    user = element.find("bdi").text

                    try:
                        wiki_date = element.find("a", {'class': 'mw-changeslist-date'}).text
                    except AttributeError:
                        wiki_date = element.find("span", {'class': 'history-deleted'}).text

                    if lang in self.formatter.lang_support_default:
                        sql_date = self.formatter.convert_date(lang, wiki_date)
                        history.append((sql_date, user))
                    else:
                        history.append((None, user, wiki_date))
            except AttributeError as e:
                log.warn(e)

            try:
                next_url = soup.find("a", {'rel': 'next'})['href']
                if next_url:
                    next_url = base_url + next_url
                    pages.append(next_url)
            except TypeError:
                break
        return history

    # Function of extracting the articles in other languages
    # in  - html page
    # out - updates the queue variable with links in other languages for the current article
    def get_page_in_other_languages(self, soup):
        try:
            div_lang = soup.find("div", {'id': 'p-lang'})
            li_list = div_lang.find_all("li")

            for li in li_list:
                a = li.find('a', href=True)
                self.queue.append(a['href'])
        except AttributeError:
            log.warn("Other languages not found!")

    # The main function of gathering information gets URL, loads the page extracts the title, content, categories,
    # history of changes, and keeps everything in the database
    def scrap(self, url):

        page = self.load_page_by_url(url)

        if not page:
            return

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

    # Startup function
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
