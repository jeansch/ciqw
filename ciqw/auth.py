# This file is part of ciqw
# Copyright (C) 2021  Jean Schurger

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301  USA

import logging
import os
import sys
import requests
import pyquery

logger = logging.getLogger(__name__)

SERVICE = "https://sso.garmin.com/sso/embed"
SGC = "https://services.garmin.com"
APIGCS = "https://api.gcs.garmin.com"


def get_ticket(username, password):
    logger.info("Getting login page")
    signin = "https://sso.garmin.com/sso/signin?service=%s" % SERVICE
    s = requests.Session()
    headers = {'User-Agent': 'Mozilla/5.0'}
    html_form = s.get(signin, headers=headers).text
    csrf = pyquery.PyQuery(html_form).find("[name=_csrf]").attr['value']
    data = {'username': username, 'password': password,
            '_csrf': csrf, 'embed': "true"}
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': signin}
    logger.info("Send login")
    req = s.post(signin, data, headers=headers)
    ticket = [e for e in req.text.split()
              if r'https:\/\/sso.garmin.com\/sso\/embed?ticket='
              in e][0].split('=')[1].split('"')[0]
    logger.info("Received ticket")
    return ticket


def get_token(ticket):
    data = {'grant_type': 'service_ticket',
            'client_id': 'CIQ_SDK_MANAGER',
            'service_ticket': ticket,
            'service_url': SERVICE}
    req = requests.post(SGC + "/api/oauth/token", data)
    return req.json()


def read_sdkmanager_config():
    sdkmini = os.path.join(os.getenv('HOME'), '.Garmin', 'ConnectIQ',
                        'sdkmanager-config.ini')
    if os.path.exists(sdkmini):
        return dict(l.split('=') for l in open(sdkmini).readlines()
                    if '=' in l)
    return {}


def write_sdkmanager_config(config):
    sdkmini = os.path.join(os.getenv('HOME'), '.Garmin', 'ConnectIQ',
                        'sdkmanager-config.ini')
    if sys.platform.lower().startswith('darwin'):
        devices_root = os.path.join(os.getenv('HOME'), 'Library',
                                    'Application Support',
                                    'Garmin', 'ConnectIQ',
                                    'sdkmanager-config.ini')
    os.makedirs(os.path.join(os.getenv('HOME'), '.Garmin', 'ConnectIQ'),
        exist_ok=True)
    open(sdkmini, "w").write("\n".join(
        "%s=%s" % (k, v) for k, v in config.items()) + "\n")


def login():
    if len(sys.argv) < 3:
        logger.error("Usage: ciwq-login [username] [password]")
        sys.exit(1)
    ticket = get_ticket(sys.argv[1], sys.argv[2])
    token = get_token(ticket)
    config = read_sdkmanager_config()
    config.update({
        'Garmin.ConnectIQ.SdkManager.accessToken': token['access_token'],
        'Garmin.ConnectIQ.SdkManager.refreshToken': token['refresh_token']})
    write_sdkmanager_config(config)


def _get_access_token():
    return read_sdkmanager_config().get(
        'Garmin.ConnectIQ.SdkManager.accessToken', '').strip()
