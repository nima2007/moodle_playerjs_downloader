from selenium.webdriver.common.by import By
from selenium import webdriver
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re

# TODO Run on every video in the chapter automatically
# TODO Download video via ffmpeg-python
# TODO download subtitle

CHROME_DRIVER_PATH = "/Users/nima/Documents/PyCharmProjects/eminemselenium/chromedriver"
DOMAIN = "https://learning.eminem.edu"
MOODLE_SESSION = "t6n9d216kjkijhgjp75a5q7ko6"


# Set up the selenium driver to control the chrome browser
def setup_driver():
    # Enable logging on Chrome to get network data
    caps = DesiredCapabilities.CHROME
    caps['loggingPrefs'] = {'performance': 'ALL'}
    caps['goog:loggingPrefs'] = {'performance': 'ALL'}

    # Set chrome driver
    driver = webdriver.Chrome(executable_path=CHROME_DRIVER_PATH, desired_capabilities=caps)
    return driver


# Put in the cookie that enables us to log in, then go to the homepage
def initial_login(driver):
    # Put in moodle cookie after going on a dummy page
    driver.get(DOMAIN + "/hi")
    driver.add_cookie({"name": "MoodleSession", "value": MOODLE_SESSION})

    # Ensure can login to main page
    driver.get(DOMAIN + "/online/course/view.php?id=551&program=scpd")


# When on a video page, grab strings that CONTAIN: stream URL, HLS key cookie, subtitle, and video title.
# The garbage around those things need to later be removed
def get_video_info(driver, video):
    # Video page
    driver.get(video)
    time.sleep(5)

    # Get javascript which contains title
    vtitle = driver.find_element_by_xpath("/html/head/script[4]").get_attribute("innerHTML")

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
    # Go through the network logs and grab anything that matches our search terms below
    for entry in driver.get_log('performance'):
        entry = entry['message']
        if "hls720.m3u8" in str(entry):
            streams.append(entry)
        if "hlskey" in str(entry) and "Network.requestWillBeSentExtraInfo" in str(entry):
            keys.append(entry)
        if ".vtt" in str(entry):
            sub.append(entry)

    return [streams, keys, sub, [vtitle]]


# Just for debugging, print the stuff in a list of lists
def print_video_info(info):
    for lst in info:
        for item in lst:
            print(str(item))
        print()
        print("-----------------------------------------------")
        print()


# Get rid of the garbage around the string containing video URL, and return just that
def pattern_match_stream(stream_720):
    regex_720 = re.compile(r"(https://[a-zA-Z0-9]+\.cloudfront\.[^\"]+hls720\.m3u8)")
    search_720 = re.search(regex_720, stream_720)
    assert search_720
    found_720 = search_720.group(1)
    print("Match stream: " + found_720)


# Get rid of the garbage around the string containing key cookie, and return just that
def pattern_match_key(key):
    regex_keys = re.compile(r'"cookie":"(.+=1;.+)"')
    search_keys = re.search(regex_keys, key)
    assert search_keys
    found_keys = search_keys.group(1)
    print("Match key: " + found_keys)


# Get rid of the garbage around the string containing subtitle URL, and return just that
def pattern_match_sub(content):
    regex_sub = re.compile(r'\"(https://[a-zA-Z0-9]+\.cloudfront\.[^\"]+\.vtt)\"')
    search_sub = re.search(regex_sub, content)
    assert search_sub
    found_sub = search_sub.group(1)
    print("Match sub: " + found_sub)


# Get rid of the garbage around the string containing video title, and return just that
def pattern_match_title(contents):
    regex_title = re.compile(r'name\\\":\\\"([a-zA-z0-9 ]+)\\\",')
    search_title = re.search(regex_title, contents)
    assert search_title
    found_title = search_title.group(1)
    print("Match title: " + found_title)


# MAIN
def main():
    driver = setup_driver()
    initial_login(driver)
    vinfo = get_video_info(driver, DOMAIN + "/online/mod/video/view.php?id=14801")
    print_video_info(vinfo)
    pattern_match_stream(vinfo[0][0])
    pattern_match_key(vinfo[1][0])
    pattern_match_title(vinfo[3][0])
    pattern_match_sub(vinfo[2][0])
    driver.quit()


def test():
    pass


# Entry point
if __name__ == "__main__":
    main()
