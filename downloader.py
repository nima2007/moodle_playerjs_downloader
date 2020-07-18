from selenium.webdriver.common.by import By
from selenium import webdriver
import unittest
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from browsermobproxy import Server
import pprint

CHROME_DRIVER_PATH = "/Users/nima/Documents/PyCharmProjects/eminemselenium/chromedriver"
DOMAIN = "https://learning.eminem.edu"


#server = Server("/Users/nima/Documents/PyCharmProjects/Xfordselenium/browsermob-proxy-2.1.4/bin/browsermob-proxy")
#server.start()
#proxy = server.create_proxy()


caps = DesiredCapabilities.CHROME
caps['loggingPrefs'] = {'performance': 'ALL'}
caps['goog:loggingPrefs'] = {'performance': 'ALL'}


#driver = webdriver.Safari()
driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, desired_capabilities=caps)


# Put in moddle cookie
driver.get(DOMAIN + "/hi")
driver.add_cookie({"name": "MoodleSession", "value": "9sb0a2jude0iuk9p82ks2207e3"})


# Ensure can login to main page
driver.get(DOMAIN + "/online/course/view.php?id=551&program=scpd")

# Video page
driver.get(DOMAIN + "/online/mod/video/view.php?id=14801")

#print(driver.get_cookies())

time.sleep(5)

driver.find_element_by_xpath("/html/body/player/div/div/button").click()  # big play btn
time.sleep(1)
driver.find_element_by_xpath("/html/body/player/div/div/div[5]/div[15]").click()  # quality cog
time.sleep(1)
driver.find_element_by_xpath("/html/body/player/div/div/div[5]/div[15]/div/ul/li[4]").click()  # 720p
time.sleep(5)

#print(driver.execute_script("var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {}; var network = performance.getEntries() || {}; return network;"))

streams = []
keys = []
sub = []
for entry in driver.get_log('performance'):
    if "hls720.m3u8" in str(entry):
        streams.append(entry)
    if "hlskey" in str(entry):
        keys.append(entry)
    if ".vtt" in str(entry):
        keys.append(entry)

pprint.pprint(streams)
pprint.pprint(keys)
pprint.pprint(sub)

driver.quit()
