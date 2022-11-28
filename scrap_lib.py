from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from time import sleep
import requests
import os.path
import random



HEADERS = requests.utils.default_headers()
HEADERS.update({"User-Agent": UserAgent().random})
CACHE_DIR = "cache/"



def file_path(cache: str, url: str) -> str:
	return cache + url.replace('/', '|')


def sleep_time() -> float:
	return round(1/random.random(), 1)


def get_from_hd(url: str, cache: str = CACHE_DIR) -> str:
	path = file_path(cache, url)
	page_source = ""
	if not os.path.isfile(path):
		return ""
	with open(path, "r") as f:
		page_source = f.read()
	return page_source


def save_on_hd(url: str, page_source: str, cache: str = CACHE_DIR) -> None:
	path = file_path(cache, url)
	with open(path, "w") as f:
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


class Requester:
	use_hd = True
	sleep_rand = True
	sleep_time = 1
	ua = UserAgent()
	enable_proxy = False
	proxies = {}
	proxy_list = {}

	def __init__(self, cache_dir: str):
		self.cache_dir = cache_dir
		self.headers = requests.utils.default_headers()
		self.change_headers()

	def use_proxies(self, proxy_list: dict):
		self.enable_proxy = True
		self.proxy_list = proxy_list
		self.change_proxies()

	def get_from_hd(self, url: str) -> str:
		path = file_path(self.cache_dir, url)
		page_source = ""
		if not os.path.isfile(path):
			return ""
		with open(path, 'r') as f:
			page_source = f.read()
		return page_source

	def save_on_hd(self, url, str, page_source: str) -> None:
		path = file_path(self.cache_dir, url)
		with open(path, 'w') as f:
			f.write(page_source)

	def change_headers(self):
		self.headers.update({"User-Agent": self.ua.random})

	def change_proxies(self):
		self.proxies = {'http': random.choice(self.proxy_list['http']),
				'https': random.choice(self.proxy_list['https'])}

	def get_response(self, url: str):
		self.change_headers()
		self.change_proxies()
		if self.enable_proxy:
			response = requests.get(url, headers=self.headers,
				proxies=self.proxies)
		else:
			response = requests.get(url, headers=self.headers)
		return response

	def request(self, url: str):
		if self.sleep_rand:
			sleep(round(1/random.random(), 1))
		else:
			sleep(self.sleep_time)
		return self.get_response(url=url)

	def get_page_soup(self, url: str) -> BeautifulSoup:
		page_source = ""
		if self.use_hd:
			page_source = self.get_from_hd(url=url)

		if not page_source:
			page_source = self.request(url=url).text
			if self.use_hd:
				self.save_on_hd(url=url, page_source=page_source)

		return BeautifulSoup(page_source, 'lxml')

