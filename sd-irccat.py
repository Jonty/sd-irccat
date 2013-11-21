#!/usr/bin/env python
import ConfigParser
import json
import time
import socket
import logging

import requests

logging.basicConfig(level=logging.INFO)
log = logging.getLogger('sd-irccat')

config = ConfigParser.ConfigParser()
config.read(['sd-irccat.conf'])

account = config.get('serverdensity', 'account')
auth = (config.get('serverdensity', 'username'), config.get('serverdensity', 'password'))

alerts_seen = set()
first_run = True

while True:
    response = requests.get('https://api.serverdensity.com/1.4/alerts/getLast?account=%s' % account, auth=auth)
    data = json.loads(response.content)
    for alert in data['data']['alerts']:
        service = alert['device']['name']
        alert = alert['alert']

        alert_uniq = alert['alertId'] + alert['timeAlertedGMT'] + alert['fixed']
        url = "https://%s/alerts/history/%s" % (account, alert['alertId'])

        if alert_uniq in alerts_seen:
            continue

        if alert['fixed'] == '0':
            alert_type = 'ALERT'
            alert_colour = 'RED'
        else:
            alert_type = 'FIXED'
            alert_colour = 'GREEN'

        alert_string = "[#BOLD#%s%s#NORMAL %s] %s (Value is %s) - %s" % \
            (alert_colour, alert_type, service, alert['checkTypeText'], alert['triggeredValue'], url)
        log.info(alert_string)

        if first_run == False:

            for channel in config.get('irccat', 'channels').split(','):
                channel = channel.strip()

                log.info('Sending alert to %s', channel)

                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((config.get('irccat', 'host'), int(config.get('irccat', 'port'))))
                s.sendall("%s %s" % (channel, alert_string))
                s.close()

        alerts_seen.add(alert_uniq)

    first_run = False
    time.sleep(10)
