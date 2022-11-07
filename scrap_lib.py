import requests
from bs4 import BeautifulSoup as BS


def get_page_soup(url) -> BS:
	response = requests.get(url)
	return BS(response.text, 'lxml')

