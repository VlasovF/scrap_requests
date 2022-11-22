import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as BS
from time import sleep
import os.path
import random


HEADERS = requests.utils.default_headers()
HEADERS.update({"User-Agent": UserAgent().random})
CACHE_DIR = "cache/"



def sleep_time() -> float:
	return round(1/random.random(), 1)


def get_from_hd(url: str, cache: str = CACHE_DIR) -> str:
	path = f"{cache}{url}"
	page_source = ""
	if not os.path.isfile(path):
		return ""
	with open(path, "r") as f:
		page_source = f.read()
	return page_source


def save_on_hd(url: str, page_source: str, cache: str = CACHE_DIR) -> None:
	with open(f"{cache}{url}", "w") as f:
		f.write(page_source)


def get_page_soup(url: str, headers: dict = HEADERS, use_hd: bool = True,
		  sleep_time: float = sleep_time()) -> BS:
	if use_hd:
		page_source = get_from_hd(url=url)
		if page_source:
			return BS(page_source, 'lxml')

	page_source = requests.get(url, headers=headers).text
	sleep(sleep_time)

	if use_hd:
		save_on_hd(url=url, page_source=page_source)

	return BS(page_source, 'lxml')

