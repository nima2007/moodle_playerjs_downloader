from selenium.webdriver.common.by import By
from selenium import webdriver
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

# TODO Get video title
# TODO Run on every video in the chapter automatically
# TODO Download via ffmpeg-python

CHROME_DRIVER_PATH = "/Users/nima/Documents/PyCharmProjects/eminemselenium/chromedriver"
DOMAIN = "https://learning.eminem.edu"

# Enable logging on Chrome to get network data
caps = DesiredCapabilities.CHROME
caps['loggingPrefs'] = {'performance': 'ALL'}
caps['goog:loggingPrefs'] = {'performance': 'ALL'}

# Set chrome driver
driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, desired_capabilities=caps)

# Put in moodle cookie after going on a dummy page
driver.get(DOMAIN + "/hi")
driver.add_cookie({"name": "MoodleSession", "value": "9sb0a2jude0iuk9p82ks2207e3"})

# Ensure can login to main page
driver.get(DOMAIN + "/online/course/view.php?id=551&program=scpd")

# Video page
driver.get(DOMAIN + "/online/mod/video/view.php?id=14801")
time.sleep(5)

# Play video and select quality
driver.find_element_by_xpath("/html/body/player/div/div/button").click()  # big play btn
time.sleep(1)
driver.find_element_by_xpath("/html/body/player/div/div/div[5]/div[15]").click()  # quality cog
time.sleep(1)
driver.find_element_by_xpath("/html/body/player/div/div/div[5]/div[15]/div/ul/li[4]").click()  # 720p
time.sleep(3)


streams = []
keys = []
sub = []
for entry in driver.get_log('performance'):
    if "hls720.m3u8" in str(entry):
        streams.append(entry)
    if "hlskey" in str(entry):
        keys.append(entry)
    if ".vtt" in str(entry):
        sub.append(entry)

for lst in [streams, keys, sub]:
    for item in lst:
        print(str(item))
    print()
    print("-----------------------------------------------")
    print()

driver.quit()
