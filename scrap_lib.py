import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup as BS


def get_page_soup(url: str, ua: UserAgent = UserAgent()) -> BS:
	headers = requests.utils.default_headers()
	headers.update({'User-Agent': ua.random})
	response = requests.get(url, headers=headers)
	return BS(response.text, 'lxml')

