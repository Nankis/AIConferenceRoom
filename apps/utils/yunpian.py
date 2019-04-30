# -*- coding: utf-8 -*-
__author__ = 'Ginseng'
import json
import requests


class YunPian(object):

    def __init__(self, api_key):
        self.api_key = api_key
        self.single_send_url = "https://sms.yunpian.com/v2/sms/single_send.json"

    def send_sms(self, password, mobile):
        parmas = {
            "apikey": self.api_key,
            "mobile": mobile,
            "text": "【AI会议室】您的密码为：{password} 。如非本人操作，请忽略本短信".format(password=password)
        }

        response = requests.post(self.single_send_url, data=parmas)
        re_dict = json.loads(response.text)
        return re_dict

# if __name__ == "__main__":
#     yun_pian = YunPian("")
#     yun_pian.send_sms("2017", "")
