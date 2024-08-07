import string
import requests
from urllib.parse import quote
import http.client
from lxml import html, etree
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

    def consumptionChart(self, meter_id: str) -> float:
        cookie = self.login()
        response = requests.get(consumption_chart_url, headers=self.getHeaders(cookie), stream=True)
        dom = etree.HTML(response.text)
        value = dom.xpath('/html/body/div[3]/div/div/div/div[3]/div/table/tbody/tr/td[.="' + meter_id + '"]')[0].getparent().xpath('.//td[.="Odczyt klienta"]')[0].getparent().xpath('.//td[contains(@class, "col-value")]')[0].text.strip()
        value = value.replace(',', '.')
        return float(value)

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
