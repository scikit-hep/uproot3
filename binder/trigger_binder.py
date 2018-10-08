#!/usr/bin/env python

import argparse
from contextlib import contextmanager
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of


class SeleniumSession():
    def __init__(self, args):
        self.options = Options()
        self.options.set_headless()
        self.options.add_argument('--no-sandbox')
        if args.chromedriver_path is not None:
            self.browser = webdriver.Chrome(
                args.chromedriver_path, chrome_options=self.options)
        else:
            self.browser = webdriver.Chrome(chrome_options=self.options)

    @contextmanager
    def wait_for_page_load(self, timeout=20):
        old_page = self.browser.find_element_by_tag_name('html')
        yield
        WebDriverWait(self.browser, timeout).until(staleness_of(old_page))

    def trigger_binder(self, url):
        with self.wait_for_page_load():
            self.browser.get(url)


def main(args):
    driver = SeleniumSession(args)
    if args.is_verbose:
        print('Chrome Headless Browser Invoked')
    driver.trigger_binder(args.url)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', dest='is_verbose',
                        action='store_true',
                        help='Print out more information')
    parser.add_argument('--chromedriver-path', dest='chromedriver_path',
                        type=str, default=None, help='System path to ChromeDriver')
    parser.add_argument('--url', dest='url',
                        type=str, default=None, help='URL for Selinium to open')
    args = parser.parse_args()

    main(args)
