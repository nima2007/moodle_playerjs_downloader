from selenium.webdriver.common.by import By
from selenium import webdriver
import time
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import re
import pycurl
import os
import logging
import subprocess
import requests

CHROME_DRIVER_PATH = "/Users/nima/Documents/PyCharmProjects/emimemselenium/chromedriver"
DOMAIN = "https://learning.emimem.edu"  # Moodle homepage of the program
MOODLE_SESSION = "5ermgm3gtqceafh3fffdk3bsh5"  # Signin Cookie
DL_PATH = "/Volumes/NAS/Nima/IC DL/automated/"
TOP_MODULES = ["557", "560"] # Which course modules to download in
#TOP_MODULES = ["561", "556"]
PROGRAM = "scpd" # Which program the course is in


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.debug('Logger started')

def get_video_ids(driver, topid):
    driver.get(DOMAIN + f"/online/course/view.php?id={topid}&program={PROGRAM}")
    html = driver.page_source
    modids = []
    modids_resource = []
    regex_modidr = re.compile(r'modtype_resource[ "]*id="module-([0-9]+)"')
    regex_modidv = re.compile(r'modtype_video[ "]*id="module-([0-9]+)"')

    all_r = re.findall(regex_modidr, html)
    all_v = re.findall(regex_modidv, html)
    return all_v, all_r


def get_pdf_url(driver, id):
    module_url = f'{DOMAIN}/online/mod/resource/view.php?id={id}'
    driver.get(module_url)
    html = driver.page_source
    regex_pdf = re.compile(r'href="(http\S+resource\S+\.[a-z]+)"')
    f_pdfurl = re.search(regex_pdf, html)
    assert f_pdfurl
    pdfurl = f_pdfurl.group(1)
    logger.info("Match pdfurl: " + pdfurl)
    return pdfurl


def download_video(url, title, cookie, dlpath):
    save_path = os.path.join(dlpath, title + ".mp4")
    command = f'ffmpeg -y -referer "{DOMAIN}" -headers $"Cookie: {cookie}\\r\\n" -i "{url}" -c copy "{save_path}"'
    logging.info(command)
    subprocess.run(command, shell=True)
    logging.info(f"Downloaded video file for {title}")

def download_subtitle(url, title, dlpath):
    savepath = os.path.join(dlpath, f"{title}.vtt")
    inputfile = open(savepath,'wb')
    curl = pycurl.Curl()
    curl.setopt(curl.URL , url)
    curl.setopt(pycurl.HTTPHEADER, ['Referer: ' + DOMAIN ])
    curl.setopt(curl.WRITEDATA,inputfile)
    curl.perform()
    inputfile.close()
    curl.close()
    logging.info(f"Downloaded subtitle file for {title}")

def download_pdf2(url, dlpath):
    basename = os.path.basename(url)
    savepath = os.path.join(dlpath, basename)
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36",
        "Connection": "keep-alive",
    }
    s = requests.Session()
    cookie = requests.cookies.create_cookie('MoodleSession', MOODLE_SESSION)
    s.cookies.set_cookie(cookie)
    with s.get(url, stream=True, headers=headers) as r:
        with open(savepath, 'wb') as f:
            for chunk in r.iter_content(4096):
                if chunk:
                    f.write(chunk)


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
    driver.get(DOMAIN + "/online/course/view.php?id=551&program=" + PROGRAM)


# When on a video page, grab strings that CONTAIN: stream URL, HLS key cookie, subtitle, and video title.
# The garbage around those things need to later be removed
def get_video_info(driver, video):
    # Video page
    driver.get(video)
    time.sleep(5)

    # Get javascript which contains title
    vtitle = driver.find_element_by_xpath("/html/head/script[4]").get_attribute("innerHTML")
    logger.info("raw title: " + vtitle)

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

    toret = dict()
    toret["stream"] = pattern_match_stream(streams[0])
    toret["key"] = pattern_match_key(keys[0])
    toret["sub"] = pattern_match_sub(sub[0])
    toret["title"] = pattern_match_title(vtitle)

    return toret


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
    logger.info("Match stream: " + found_720)
    return found_720


# Get rid of the garbage around the string containing key cookie, and return just that
def pattern_match_key(key):
    regex_keys = re.compile(r'"cookie":"(.+=1;.+)"')
    search_keys = re.search(regex_keys, key)
    assert search_keys
    found_keys = search_keys.group(1)
    logger.info("Match key: " + found_keys)
    return found_keys


# Get rid of the garbage around the string containing subtitle URL, and return just that
def pattern_match_sub(content):
    print(content)
    regex_sub = re.compile(r'\"x?(https://[a-zA-Z0-9]+\.cloudfront\.[^\"]+\.vtt)\"')
    search_sub = re.search(regex_sub, content)
    assert search_sub
    found_sub = search_sub.group(1)
    logger.info("Match sub: " + found_sub)
    return found_sub


# Get rid of the garbage around the string containing video title, and return just that
def pattern_match_title(contents):
    regex_title = re.compile(r'\{\\\"name\\\":\\\"(.+?)\\\",')
    search_title = re.search(regex_title, contents)
    assert search_title
    found_title = search_title.group(1)
    logger.info("Match title: " + found_title)
    return found_title


# MAIN
def main():
    driver = setup_driver()
    initial_login(driver)
    #module_ids = ["14801", "14926"]
    for top_module in TOP_MODULES:
        localdlpath = os.path.join(DL_PATH, top_module)
        if not os.path.exists(localdlpath):
            os.mkdir(localdlpath)
        module_ids, resource_ids = get_video_ids(driver, top_module)
        for id in resource_ids:
            pdfurl = get_pdf_url(driver, id)
            download_pdf2(pdfurl, localdlpath)
        for id in module_ids:
            module_url = f'{DOMAIN}/online/mod/video/view.php?id={id}'
            vinfo = get_video_info(driver, module_url)
            vinfo["title"] = vinfo["title"].replace('/', '')
            download_subtitle(vinfo["sub"], vinfo["title"], localdlpath)
            download_video(vinfo["stream"], vinfo["title"], vinfo["key"], localdlpath)
    driver.quit()


def test():
    pass


# Entry point
if __name__ == "__main__":
    main()
