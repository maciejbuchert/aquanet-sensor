import string
import requests
from urllib.parse import quote, urljoin
import http.client
from lxml import etree

from bs4 import BeautifulSoup

login_url = "https://ebok.aquanet.pl/user/login"
consumption_chart_url = "https://ebok.aquanet.pl/zuzycie/odczyty"


class AquanetApi:

    def __init__(self, username, password, cookie=None) -> None:
        self.username = username
        self.password = password
        self.cookie = cookie

    def login(self) -> string:
        if self.cookie is not None:
            return self.cookie

        login_data = self.loginData()
        headers = self.getHeaders(login_data['cookie'])
        payload = {
            "csrfp_token": login_data['token'],
            "user-login-email[email]": self.username,
            "user-login-email[password]": self.password,
            "user-login-email[submit]": 'Zaloguj'
        }

        encoded_payload = ''

        for key, value in payload.items():
            encoded_payload += quote(str(key), safe='') + '=' + quote(str(value), safe='') + '&'

        encoded_payload = encoded_payload[:-1]

        conn = http.client.HTTPSConnection("ebok.aquanet.pl")
        conn.request("POST", "/user/login", encoded_payload, headers)
        response = conn.getresponse()

        self.cookie = login_data['cookie']
        return self.cookie

    def loginData(self) -> dict:
        response = requests.get(login_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        cookie = ""
        for c in response.cookies:
            cookie += "%s=%s;" % (c.name, c.value)

        return {
            'cookie': cookie,
            'token': soup.select_one('input[name="csrfp_token"]')['value'],
        }

    def consumptionChart(self) -> string:
        cookie = self.login()
        token = self.getConsumptionChartToken()

        payload = {
            "csrfp_token": token,
            "daterange[from]": "06.02.2024",
            "daterange[to]": "06.02.2024",
            "daterange[point]": "362428",
            "daterange[submit]": "Filtruj"
        }

        encoded_payload = ''

        for key, value in payload.items():
            encoded_payload += quote(str(key), safe='') + '=' + quote(str(value), safe='') + '&'

        encoded_payload = encoded_payload[:-1]

        print(encoded_payload)
        print(self.getHeaders(cookie, 'https://ebok.aquanet.pl/zuzycie/odczyty'))
        conn = http.client.HTTPSConnection("ebok.aquanet.pl")
        conn.request("POST", "/zuzycie/odczyty", encoded_payload, self.getHeaders(cookie, 'https://ebok.aquanet.pl/zuzycie/odczyty'))
        response = conn.getresponse()

        soup = BeautifulSoup(response.read().decode("utf-8"), "html.parser")
        dom = etree.HTML(str(soup))
        print(dom.xpath('/html/body/div[3]/div[2]/div/div/div[3]/div/table/tbody/tr/td[3]')[0].text)

    def getConsumptionChartToken(self) -> string:
        cookie = self.login()
        response = requests.get(consumption_chart_url, headers=self.getHeaders(cookie))
        soup = BeautifulSoup(response.content, 'html.parser')

        return soup.select_one('input[name="csrfp_token"]')['value']

    def getHeaders(self, cookie: str, referer: str = 'https://ebok.aquanet.pl/user/login') -> dict:
        return {
          'authority': 'ebok.aquanet.pl',
          'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
          'accept-language': 'pl-PL,pl;q=0.9',
          'cache-control': 'no-cache',
          'content-type': 'application/x-www-form-urlencoded',
          'cookie': cookie,
          'origin': 'https://ebok.aquanet.pl',
          'pragma': 'no-cache',
          'referer': referer,
          'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
          'sec-ch-ua-mobile': '?0',
          'sec-ch-ua-platform': '"macOS"',
          'sec-fetch-dest': 'document',
          'sec-fetch-mode': 'navigate',
          'sec-fetch-site': 'same-origin',
          'sec-fetch-user': '?1',
          'upgrade-insecure-requests': '1',
          'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
