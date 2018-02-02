#!/usr/bin/env python3
'''
Script to email the screencap associated with the most recent FM_Web_Check alarm to a list of interested parties.

Created on November 14, 2017

@author: mhandler
'''

from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging
import os
import smtplib

from_addr = '<from address>'
to_addrs = [<list of destination addresses>]

LAST_SCREENCAP_FILE_PATH = '/tmp/FM_last_screencap_sent.tmp'

def main():

    logging.basicConfig(filename="/tmp/RPM_website_check.log", level=logging.INFO, format='%(asctime)s %(message)s')

    logging.info("Selecting screencap to send...")
    screencap_names = list(filter(lambda filename: filename.startswith("RPM_screenshot_"), os.listdir('/tmp')))
    screencap_infos = list(map(lambda screencap_name: ['/tmp/' + screencap_name, os.stat('/tmp/'+screencap_name)],screencap_names))

    newest_sc_time = 0
    newest_sc_name = None
    for info in screencap_infos:
        if info[1].st_mtime > newest_sc_time:
            newest_sc_time = info[1].st_mtime
            newest_sc_name = info[0]

    last_sent_info = None
    lsf = Path(LAST_SCREENCAP_FILE_PATH)
    if (lsf.exists()):
        last_sent_info = os.stat(LAST_SCREENCAP_FILE_PATH)

    if (newest_sc_name != None and (last_sent_info == None or last_sent_info.st_mtime < newest_sc_time)):
        logging.info("Sending screencap: " + newest_sc_name)
        msg = MIMEMultipart()
        msg['Subject'] = 'Screencap from most recent RPM Web Check alarm'
        msg['From'] = from_addr
        msg['To'] = ", ".join(to_addrs)

        fp = open(newest_sc_name, 'rb')
        img = MIMEImage(fp.read())
        fp.close()
        msg.attach(img)

        s = smtplib.SMTP('smtpdc.salientsystems.com')
        s.sendmail(from_addr, to_addrs, msg.as_string())
        s.quit()

        # keep a record of the last time we sent a screencap
        with open(LAST_SCREENCAP_FILE_PATH, "w") as f:
            f.write("")
    else:
        logging.info("No screencap to send")


main()