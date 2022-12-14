from fake_useragent import UserAgent
from bs4 import BeautifulSoup

from time import sleep
import requests
import os.path
import random
import logging



logging.basicConfig(filename='scraper.log',
			filemode='a',
			format='%(asctime)s - %(message)s',
			datefmt='%H:%M:%S',
			level=logging.INFO)

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
		  sleep_time: float = sleep_time()) -> BeautifulSoup:
	if use_hd:
		page_source = get_from_hd(url=url)
		if page_source:
			return BeautifulSoup(page_source, 'lxml')

	page_source = requests.get(url, headers=headers).text
	sleep(sleep_time)

	if use_hd:
		save_on_hd(url=url, page_source=page_source)

	return BeautifulSoup(page_source, 'lxml')


def get_from_free_proxy_list() -> dict:
	proxies = {'http': [], 'https': []}
	url = "https://free-proxy-list.net/"
	page = get_page_soup(url, sleep_time=0.1, use_hd=False)
	table = page.select('.table-striped')[0]
	trs = table.find_all('tr')
	ips = [tr.find_all('td') for tr in trs[1:]]
	res = [{'ip': t[0].text, 'port': t[1].text, 'https': t[-2].text} for t in ips]
	res = [{
		'ip': t[0].text,
		'port': t[1].text,
		'https': t[-2].text,
		'anonymity': t[-4].text} for t in ips[1:]]
	for ip in res:
		if ip['https'] == "yes" and ip['anonymity'] != "transparent":
			proxies['https'].append(f"http://{ip['ip']}:{ip['port']}")
		elif ip['https'] == "no" and ip['anonymity'] != "transparent":
			proxies['http'].append(f"http://{ip['ip']}:{ip['port']}")
	return proxies


def get_from_one_hidemy_page(soup: BeautifulSoup) -> dict:
	proxies = dict()
	trs = soup.select('.table_block')[0].select('tr')
	trs = [tr.find_all('td') for tr in trs]
	res = [{'ip': tr[0].text,
		'port': tr[1].text,
		'https': tr[-3].text}
		for tr in trs[1:]]

	proxies['http'] = [f"http://{ip['ip']}:{ip['port']}" for ip in res
				if ip['https'] == "HTTP"]

	proxies['https'] = [f"http://{ip['ip']}:{ip['port']}" for ip in res
				if ip['https'] == "HTTPS"]
	return proxies


def get_hidemy_page_links(soup: BeautifulSoup) -> list:
	lis = soup.select('.pagination')[0].find_all('li')
	url = "https://hidemy.name"
	urls = [url + li.select('a')[0]['href'] for li in lis[:-1]]
	return urls


def get_from_hidemy() -> dict:
	proxies = {'http': [], 'https': []}
	url = 'https://hidemy.name/ru/proxy-list/?type=hs&anon=34#list'
	page = get_page_soup(url, sleep_time=0.1, use_hd=False)
	urls = get_hidemy_page_links(page)
	for url in urls:
		page = get_page_soup(url, sleep_time=0.1, use_hd=False)
		pp = get_from_one_hidemy_page(page)
		proxies['http'] += pp['http']
		proxies['https'] += pp['https']
	return proxies


def get_all_proxies() -> dict:
	fpl_pl = get_from_free_proxy_list()
	hmy_pl = get_from_hidemy()
	proxies = {'http': fpl_pl['http'] + hmy_pl['http'],
			'https': fpl_pl['https'] + hmy_pl['https']}
	verified = []
	for proxy in proxies['https']:
		try:
			proxies = {'http': proxy, 'https': proxy}
			response = requests.get('https://api.myip.com', timeout=10)
			if response.status_code == 200:
				verified.append(proxy)
				logging.info('Verified ' + proxy)
			sleep(0.5)
		except Exception as e:
			pass
	proxies['https'] = verified
	return proxies


class MaxRequestsUrl(Exception):
	pass


class ResponseBadStatusCode(Exception):
	pass


class Requester:
	use_hd = True
	sleep_rand = True
	sleep_time = 1
	ua = UserAgent()
	enable_proxy = False
	max_requests_url = 99
	max_unverified_requests = 2
	refill_proxy_list = 1
	rotation = 5
	timeout = 3
	verify = True
	del_proxy_strategy = True
	min_timeout_strategy = True
	proxies = {}
	proxy_list = {}
	verified_proxy_list = []

	def __init__(self, cache_dir: str):
		self.cache_dir = cache_dir
		self.headers = requests.utils.default_headers()
		self.change_headers()

	def update(self,newdata):
		for key,value in newdata.items():
			setattr(self, key, value)

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
		logging.info("hdget " + url)
		return page_source

	def save_on_hd(self, url: str, page_source: str) -> None:
		path = file_path(self.cache_dir, url)
		with open(path, 'w') as f:
			f.write(page_source)

	def change_headers(self):
		self.headers.update({"User-Agent": self.ua.random})

	def change_proxies(self):
		self.proxies = {'http': random.choice(self.proxy_list['http']),
				'https': random.choice(self.proxy_list['https'])}

		if len(self.proxy_list['https']) <= self.rotation:
			for proxy in self.verified_proxy_list:
				if proxy not in self.proxy_list['https']:
					self.proxy_list['https'].append(proxy)
			self.verified_proxy_list = []

		if len(self.proxy_list['https']) <= self.refill_proxy_list:
			proxy_list = get_all_proxies()
			self.use_proxies(proxy_list=proxy_list)

	def change_to_verified_proxies(self):
		if not self.verified_proxy_list:
			self.change_proxies()
		else:
			verified_proxy = random.choice(self.verified_proxy_list)
			self.proxies = {'http': verified_proxy,
                                	'https': verified_proxy}

	def delete_proxy_from_list(self, type: str):
		proxy = self.proxies[type]
		self.proxy_list[type] = [p for p in self.proxy_list[type] if p != proxy]
		logging.info('Delete proxy ' + proxy + ' https n: ' + str(
						len(self.proxy_list['https'])))

	def get_response(self, url: str, req: int = 0):
		self.change_headers()
		if req < self.max_unverified_requests:
			self.change_proxies()
		else:
			self.change_to_verified_proxies()

		if self.enable_proxy:
			try:
				response = requests.get(url, headers=self.headers,
					proxies=self.proxies, timeout=self.timeout,
					verify=self.verify)
			except Exception as e:
				type = url.split('://')[0]
				if self.del_proxy_strategy:
					self.delete_proxy_from_list(type=type)
				response = self.request(url=url, req=req+1)
		else:
			response = requests.get(url, headers=self.headers,
					timeout=self.timeout, verify=self.verify)
		return response

	def request(self, url: str, req: int = 0):
		if req == self.max_requests_url:
			logging.info(f"MaxRequestsUrl {req}")
			raise MaxRequestsUrl
		if self.sleep_rand:
			sleep(round(1/random.random(), 1))
		else:
			sleep(self.sleep_time)
		logging.info(str(req+1) + ' get ' + url)
		return self.get_response(url=url, req=req)

	def get_page_soup(self, url: str) -> BeautifulSoup:
		page_source = ""
		if self.use_hd:
			page_source = self.get_from_hd(url=url)

		if not page_source:
			response = self.request(url=url)
			if response.status_code != 200:
				logging.info(f"StatusCode {response.status_code}")
				raise ResponseBadStatusCode
			elif self.proxies not in self.verified_proxy_list:
				self.verified_proxy_list.append(self.proxies['https'])
			page_source = response.text
			if self.use_hd:
				self.save_on_hd(url=url, page_source=page_source)

		return BeautifulSoup(page_source, 'lxml')

