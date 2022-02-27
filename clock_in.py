import requests
import json
import argparse
import re
import cv2
import numpy as np
from captcha import recognize

# 初始化变量
parser = argparse.ArgumentParser()
parser.add_argument('--username', type=str, default=None)
parser.add_argument('--password', type=str, default=None)
parser.add_argument('--province', type=str, default=None)
parser.add_argument('--city', type=str, default=None)
parser.add_argument('--county', type=str, default=None)
args = parser.parse_args()

def captchaOCR():
    captcha = ''
    token   = '' 
    while len(captcha) != 4:
        token = requests.get('https://fangkong.hnu.edu.cn/api/v1/account/getimgvcode').json()['data']['Token']
        image_raw = requests.get(f'https://fangkong.hnu.edu.cn/imagevcode?token={token}').content
        image = cv2.imdecode(np.frombuffer(image_raw, np.uint8), cv2.IMREAD_COLOR)
        try:
            captcha = recognize(image)
        except Exception as err:
            print(err)

    return token, captcha

def login():
    login_url = 'https://fangkong.hnu.edu.cn/api/v1/account/login'
    token, captcha = captchaOCR()
    login_info = {"Code":args.username,"Password":args.password,"VerCode":captcha,"Token":token}
    
    set_cookie = requests.post(login_url, json=login_info).headers['set-cookie']
    regex = r"\.ASPXAUTH=(.*?);"
    ASPXAUTH = re.findall(regex, set_cookie)[2]

    headers = {'Cookie': f'.ASPXAUTH={ASPXAUTH}; TOKEN={token}'}
    return headers

def setLocation():
    location = json.loads(requests.get(f'http://api.tianditu.gov.cn/geocoder?ds={{"keyWord":\"{args.province+args.city+args.county}\"}}&tk=2355cd686a32d016021bffbc4a69d880').text)["location"]
    real_address = "1区3栋623" # 在此填写详细地址
    return location["lon"], location["lat"], real_address

def main():
    clockin_url = 'https://fangkong.hnu.edu.cn/api/v1/clockinlog/add'
    headers = login()
    lon, lat, real_address = setLocation()
    clockin_data = {
                    "Longitude":lon,
                    "Latitude":lat,
                    "RealProvince":args.province,
                    "RealCity":args.city,
                    "RealCounty":args.county,
                    "RealAddress":real_address,
                    "BackState":1,
                    "MorningTemp":"36.5",
                    "NightTemp":"36.5",
                    "tripinfolist":[],
                    "QRCodeColor":"绿色"
                    }

    clockin = requests.post(clockin_url, headers=headers, json=clockin_data)

    if clockin.status_code == 200:
        if '成功' in clockin.text or '已提交' in clockin.text:
            isSucccess = 0
        else:
            isSucccess = 1
            print(json.loads(clockin.text)['msg'])
    else:
        isSucccess = 1
    print(json.loads(clockin.text)['msg'])

    return isSucccess

main()

# for i in range(10):
#     try:    
#         a = main()
#         if a == 0:
#             break
#         elif i == 9 and a == 1:
#             raise ValueError("打卡失败")
#         else:
#             continue
#     except:
#         continue
