from machine import Pin, I2C, ADC
import network
import time
import urequests
import random
from ssd1306 import SSD1306_I2C
import framebuf


# 이메일, 위도, 경도 표시하기(자신의 스마트팜 위치를 검색해서 넣어주세요.)
nickname = 'mtinet'  # 닉네임 변수를 자신만의 닉네임으로 수정하세요.
lat = 37.49836
long = 126.9253


# 제어할 핀 번호 설정
led = Pin(1, Pin.OUT) # 생장 LED제어 핀
fan = Pin(5, Pin.OUT) # 팬 제어
moisture = ADC(26) # 수분 감지
temperature = ADC(27) # 온도 감지
light = ADC(28) # 조도 감지

conversion_factor = 3.3 / 65535 # 측정값 보정 계산식


# OLED 기본 설정
WIDTH  = 128                                            # oled display width
HEIGHT = 64                                             # oled display height

i2c = I2C(0, scl=Pin(17), sda=Pin(16), freq=200000)       # Init I2C using pins GP8 & GP9 (default I2C0 pins)
print("I2C Address      : "+hex(i2c.scan()[0]).upper()) # Display device address
print("I2C Configuration: "+str(i2c))                   # Display I2C config

oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)                  # Init oled display


# Raspberry Pi logo as 32x32 bytearray
buffer = bytearray(b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00|?\x00\x01\x86@\x80\x01\x01\x80\x80\x01\x11\x88\x80\x01\x05\xa0\x80\x00\x83\xc1\x00\x00C\xe3\x00\x00~\xfc\x00\x00L'\x00\x00\x9c\x11\x00\x00\xbf\xfd\x00\x00\xe1\x87\x00\x01\xc1\x83\x80\x02A\x82@\x02A\x82@\x02\xc1\xc2@\x02\xf6>\xc0\x01\xfc=\x80\x01\x18\x18\x80\x01\x88\x10\x80\x00\x8c!\x00\x00\x87\xf1\x00\x00\x7f\xf6\x00\x008\x1c\x00\x00\x0c \x00\x00\x03\xc0\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")


# OLED에 출력하기
oled.fill(0)
# 프레임버퍼로 로고 불러오기(이미지 사이즈는  32x32)
fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)
# 프레임 버퍼에서 OLED 디스플레이로 이미지 옮기기
oled.blit(fb, 96, 0)
# 글자 넣기
oled.text("SmartFarm", 0, 25)
oled.text("  has been", 0, 35)
oled.text("    initialized.", 0, 45)
# 이미지와 글자가 보여지도록 하기
oled.show()


# 와이파이 연결하기
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    # 와이파이 연결하기, 앞에는 SSID, 뒤는 Password를 입력함
    # wlan.connect("KT_GiGA_DC1E", "027612688m") # 염창중 와이파이
    wlan.connect("U+Net454C", "DDAE014478") # 집 와이파이
    print("Waiting for Wi-Fi connection", end="...")
    print()
    while not wlan.isconnected():
        print(".", end="")
        time.sleep(1)
else:
    print(wlan.ifconfig())
    print("WiFi is Connected")
    print()


# RTDB주소
url = "https://smartfarm-f867f-default-rtdb.firebaseio.com/"
mapUrl = "https://smartfarmlocation-default-rtdb.firebaseio.com/"


# RTDB 초기 세팅이 안되어 있는 경우 초기 세팅하기
myobjInitialize = {
    'led': 0,
    'fan': 0
    }
# myobjInitialize를 RTDB로 보내 객체 교체하기, patch는 특정 주소의 데이터가 변경됨
urequests.patch(url+"smartFarm.json", json = myobjInitialize).json()
urequests.patch(mapUrl+"/"+nickname+"/"+"smartFarm.json", json = myobjInitialize).json()
print("SmartFarm has been initialized.")


# RTDB 위치 정보 초기 세팅하기
myLocation = {
    'lat': lat,
    'long': long
    }

# myLocation를 RTDB로 보내 객체 교체하기, patch는 특정 주소의 데이터가 변경됨
urequests.patch(url+"location.json", json = myLocation).json()
urequests.patch(mapUrl+"/"+nickname+".json", json = myLocation).json()
print("Location Info has been sent.")
print()


# RTDB 내역 가져오기
response = urequests.get(url+".json").json()
# byte형태의 데이터를 json으로 변경했기 때문에 메모리를 닫아주는 일을 하지 않아도 됨
# print(response)
# print(response['smartFarm'])
# print(response['smartFarm']['led'])


while True:
    # 현재 DB의 정보를 가져옴
    response = urequests.get(url+".json").json() # RTDB 데이터 가져오기
    moistureValue = round((1 - moisture.read_u16()/65535) * 100) # 수분센서 값 읽어오기
    temperatureValue = round((temperature.read_u16() * conversion_factor) * 100) # 온도센서 값 읽어오기
    lightValue = round((light.read_u16()/65535) * 100) # 조도센서 값 읽어오기

    # 읽어온 RTDB값과 센서 값 콘솔에 출력하기
    print("Status Check")
    print("LED:", response['smartFarm']['led'], "Fan:", response['smartFarm']['fan'], "Moisture:", moistureValue, "Temperature:", temperatureValue, "Light:", lightValue )
    print()


    # OLED에 출력하기
    oled.fill(0)
    # 프레임버퍼로 로고 불러오기(이미지 사이즈는  32x32)
    fb = framebuf.FrameBuffer(buffer, 32, 32, framebuf.MONO_HLSB)
    # 프레임 버퍼에서 OLED 디스플레이로 이미지 옮기기
    oled.blit(fb, 96, 0)
    # 글자 넣기
    oled.text("Light: ", 0, 5)
    oled.text(str(round(lightValue,2)), 75, 5)
    oled.text("Temp: ", 0, 20)
    oled.text(str(round(temperatureValue,2)), 75, 20)
    oled.text("Moisture: ", 0, 35)
    oled.text(str(round(moistureValue,2)), 75, 35)


    # 현재 RTDB의 led 키 값의 상태에 따라 LED 핀(1번)을 제어
    if (response['smartFarm']['led'] == 0) :
        led.value(0)
        oled.text("LED Off", 5, 50)
    else :
        led.value(1)
        oled.text("LED On", 5, 50)

    # 현재 RTDB의 fan 키 값의 상태에 따라 Fan 핀(5번)을 제어
    if (response['smartFarm']['fan'] == 0) :
        fan.value(0)
        oled.text("Fan Off", 70, 50)
    else :
        fan.value(1)
        oled.text("Fan On", 70, 50)

    # OLED에 이미지와 글자가 보여지도록 하기
    oled.show()


    # 실시간으로 확인된 각 객체 값을 딕셔너리에 넣기
    myobj = {
        'mois': moistureValue,
        'temp': temperatureValue,
        'light': lightValue
        }

    # myobj를 RTDB로 보내 객체 값 교체하기, patch는 특정 주소의 데이터가 변경됨
    urequests.patch(url+"smartFarm.json", json = myobj).json()
    urequests.patch(mapUrl+"/"+nickname+"/"+"smartFarm.json", json = myobj).json()

    # 교체한 객체값 콘솔에 출력하기
    print("Message Send")
    print(myobj)
    print()
