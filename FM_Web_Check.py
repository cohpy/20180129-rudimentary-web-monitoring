#!/usr/bin/env python3
'''
Script to log in to the RPM website to check its health

Created on November 14, 2017

@author: mhandler
'''

from pyzabbix import ZabbixMetric, ZabbixSender
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import sys
import time
import uuid

SUCCESS=0
NOT_REACHED = 1
LOGIN_SETUP_FAILED = 2
LOGIN_FAILED = 3
UNEXPECTED_PAGE_CONTENTS = 4
NO_BROWSER_CONNECTION = 5

logged_in = False

def logout(driver):
    logout_link = driver.find_element_by_id("LBLogout")
    logging.info("Logging out")
    logout_link.click()

def cleanup_and_exit(driver, display, message, zabbix_result):
    try:
        if driver != None:
            if zabbix_result != SUCCESS:
                driver.save_screenshot('/tmp/RPM_screenshot_' + str(uuid.uuid4()) + '.png')

            if logged_in:
                logout(driver)

            driver.close()
    except Exception:
        pass
    finally:
        logging.info(message)
        display.stop()

    packet = [ZabbixMetric('vtest', 'FM.web.checker', zabbix_result)]
    result = ZabbixSender(zabbix_server='zabbix-dc').send(packet)

    sys.exit(zabbix_result)

def main():
    global logged_in

    # set up infrastructure -- virtual display and logging
    display = Display(visible=0, size=(800, 600))
    display.start()
    logging.basicConfig(filename="/tmp/RPM_website_check.log", level=logging.INFO, format='%(asctime)s %(message)s')

    logging.info("Check RPM website...")


    logging.info("Connecting to browser...")
    driver = None
    try:
        driver = webdriver.Firefox()
    except Exception as e:
        cleanup_and_exit(driver, display, "Couldn't connect to browser: " + str(e), NO_BROWSER_CONNECTION)

    logging.info("Connecting to site...")
    try:
        driver.get("<url>")
    except Exception as e:
        cleanup_and_exit(driver, display, "Couldn't reach page: " + str(e), NOT_REACHED)


    logging.info("Preparing to log in...")
    try:
        name_field = driver.find_element_by_name("tb_login")
        password_field = driver.find_element_by_name("tb_password")
        name_field.send_keys("<username>")
        password_field.send_keys("<password>")
        sign_in_button =  driver.find_element_by_name("b_login")
    except Exception as e:
        cleanup_and_exit(driver, display, "Login setup failed: " + str(e), LOGIN_SETUP_FAILED)

    logging.info("Logging in...")
    try:
        sign_in_button.click()
        time.sleep(10)
        if "Login" in driver.title:
            logging.info(driver.title)
            raise ValueError("Login failed")
    except Exception as e:
        cleanup_and_exit(driver, display, str(e), LOGIN_FAILED)

    logging.info("Login succeeded")
    logged_in = True

    try:
        logging.info("Waiting for anchors to load...")
        element = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
    except Exception as e:
        cleanup_and_exit(driver, display, "Page contents not as expected: " + str(e), UNEXPECTED_PAGE_CONTENTS)

    # Do some rudimentary checks to verify that the page has loaded normally
    try:
        logging.info("Checking page contents...")
        table_title = driver.find_element_by_id("LblTitle")
        if table_title.text != "Units Dashboard":
            raise  ValueError("Table text is wrong, looking for 'Units Dashboard', found '" + table_title.text + "'")
        links = driver.find_elements_by_tag_name("a")
        milepost = False
        collector = False
        mode = False
        for elem in links:
            if elem.text == "Milepost":
                milepost = True
            if elem.text == "Collector":
                collector = True
            if elem.text == "Mode":
                mode = True
        if not (milepost and collector and mode):
            raise ValueError("Column headers not as expected")
    except Exception as e:
        cleanup_and_exit(driver, display, "Page contents not as expected: " + str(e), UNEXPECTED_PAGE_CONTENTS)

    # success
    cleanup_and_exit(driver, display, "Success: Page contents verified", SUCCESS)

main()
