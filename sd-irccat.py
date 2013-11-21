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
response = requests.get('https://api.serverdensity.com/1.4/alerts/getLast?account=%s' % account, auth=auth)

alerts_seen = set()

while True:
    data = json.loads(response.content)
    for alert in data['data']['alerts']:
        service = alert['device']['name']
        alert = alert['alert']

        alert_uniq = alert['alertId'] + alert['timeAlertedGMT']
        url = "https://%s/alerts/history/%s" % (account, alert['alertId'])

        if alert['fixed'] == '1' or alert_uniq in alerts_seen:
            continue

        alert_string = "[%s] %s (Value is %s) - %s" % (service, alert['checkTypeText'], alert['triggeredValue'], url)
        log.info(alert_string)

        for channel in config.get('irccat', 'channels').split(','):
            channel = channel.strip()

            log.info('Sending alert to %s', channel)

            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((config.get('irccat', 'host'), int(config.get('irccat', 'port'))))
            s.sendall("%s %s" % (channel, alert_string))
            s.close()

        alerts_seen.add(alert_uniq)

    time.sleep(10)
