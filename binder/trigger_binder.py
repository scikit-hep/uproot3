#!/usr/bin/env python

import argparse
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def main(args):
    options = Options()
    options.set_headless()
    options.add_argument('--no-sandbox')
    if args.chromedriver_path is not None:
        driver = webdriver.Chrome(args.chromedriver_path, chrome_options=options)
    else:
        driver = webdriver.Chrome(chrome_options=options)
    if args.is_verbose:
        print('Chrome Headless Browser Invoked')
    driver.get(args.url)
    time.sleep(10)
    driver.close()


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
