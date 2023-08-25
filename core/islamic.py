from random import choice

import names
import requests
import pyuseragents
from bs4 import BeautifulSoup

from warnings import filterwarnings
filterwarnings("ignore", category=RuntimeWarning)

from pypasser import reCaptchaV3

from core.utils import str_to_file, logger
from string import ascii_lowercase, digits

from core.utils import MailUtils

from inputs.config import (
    MOBILE_PROXY,
    MOBILE_PROXY_CHANGE_IP_LINK
)


class Islamic(MailUtils):
    referral = None

    def __init__(self, email: str, imap_pass: str, proxy: str = None):
        super().__init__(email, imap_pass)
        self.proxy = Islamic.get_proxy(proxy)

        self.first_name, self.last_name = names.get_full_name().split(" ")
        self.password = Islamic.generate_password(9)

        self.headers = {
            'authority': 'backend.prod.haqqex.tech',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'en-US,en;q=0.9,uk;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://haqqex.com',
            'referer': 'https://haqqex.com/',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': pyuseragents.random(),
        }

        self.session = requests.Session()

        self.session.headers.update(self.headers)
        self.session.proxies.update({'https': self.proxy, 'http': self.proxy})

    @staticmethod
    def get_proxy(proxy: str):
        if MOBILE_PROXY:
            Islamic.change_ip()
            proxy = MOBILE_PROXY

        if proxy is not None:
            return f"http://{proxy}"

    @staticmethod
    def change_ip():
        requests.get(MOBILE_PROXY_CHANGE_IP_LINK)

    def send_approve_link(self):
        url = f'https://backend.prod.haqqex.tech/account/api/v1/registration/{Islamic.referral}'

        headers = self.session.headers
        headers['x-captcha-token'] = Islamic.solve_recaptcha_v3()

        json_data = {
            'firstName': self.first_name,
            'lastName': self.last_name,
            'email': self.email,
            'password': self.password,
        }

        response = self.session.post(url, headers=headers, json=json_data)

        return response.json().get("id")

    @staticmethod
    def solve_recaptcha_v3():
        return str(reCaptchaV3(
            'https://www.google.com/recaptcha/api2/anchor?ar=1&k=6LcNuCUjAAAAAF0xFJbMAHQae8BUFRLXB8kP1Wca&'
            'co=aHR0cHM6Ly9oYXFxZXguY29tOjQ0Mw..&hl=uk&v=0hCdE87LyjzAkFO5Ff-v7Hj1&size=invisible&cb=p90r4j8nl24o'))

    def verify_email(self):
        verify_link = self.get_verify_link()
        return self.approve_email(verify_link)

    def get_verify_link(self):
        result = self.get_msg(from_="noreply@haqqex.com", limit=3)
        html = result["msg"]
        soup = BeautifulSoup(html, 'lxml')
        a = soup.select_one('.confirm-button td a')
        return a["href"]

    def approve_email(self, verify_link: str):
        url = f"https://backend.prod.haqqex.tech/account/api/v1/registration/confirm"

        jwt_token = verify_link.split("/")[-1]

        json_data = {
            'token': jwt_token,
        }

        response = self.session.post(url, json=json_data)

        return response.json()["isFirstTimeLogin"]

    def logs(self):
        file_msg = f"{self.email}|{self.password}|{self.proxy}"
        str_to_file(f"./logs/success.txt", file_msg)
        logger.success(f"{self.email} | Register")

    def logs_fail(self, msg: str = ""):
        file_msg = f"{self.email}|{self.password}|{self.proxy}"
        str_to_file(f"./logs/failed.txt", file_msg)
        logger.error(f"{self.email} | {msg}")

    @staticmethod
    def generate_password(k=10):
        return ''.join([choice(ascii_lowercase + digits) for _ in range(k)])
