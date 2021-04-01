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
import zipfile
import requests
from ciqw.auth import _get_access_token

logger = logging.getLogger(__name__)

SGC = "https://services.garmin.com"
APIGCS = "https://api.gcs.garmin.com"

SSL_VERIFY = not sys.platform.lower().startswith('darwin')

# Function hidden here, not used
# def get_customer_account(token):
#     headers = {'x-garmin-client-id': 'CIQ_SDK_MANAGER',
#                'authorization': 'Bearer %s' % token['access_token']}
#     req = requests.get(
#         SGC + "/accountProcessServices/customerAccounts/%s" %
#         token['customerId'], headers=headers)
#     return req.json()

# get_customer_account(token)


def get_device_list(token):
    headers = {'accept': 'application/json',
               'authorization': 'Bearer %s' % token}
    req = requests.get(
        APIGCS + "/ciq-product-onboarding/devices",
        headers=headers, verify=SSL_VERIFY)
    return req.json()


def get_device_zip(token, device):
    headers = {'accept': 'application/json',
               'authorization': 'Bearer %s' % token}
    req = requests.get(
        APIGCS +
        "/ciq-product-onboarding/devices/%s/ciqInfo" % device,
        headers=headers, verify=SSL_VERIFY)
    return req.content


def get_font_list(token):
    headers = {'accept': 'application/json',
               'authorization': 'Bearer %s' % token}
    req = requests.get(
        APIGCS + "/ciq-product-onboarding/fonts",
        headers=headers, verify=SSL_VERIFY)
    return req.json()


def install_fonts_and_devices():
    token = _get_access_token()
    if not token:
        logger.error("You need to login to install fonts and devices")
        sys.exit(1)
    _install_fonts_and_devices(token)


def _install_fonts_and_devices(token):
    _install_fonts(token)
    _install_devices(token)


def _install_fonts(token):
    fonts_root = os.path.join(os.getenv('HOME'), '.Garmin',
                              'ConnectIQ', 'Fonts')
    if sys.platform.lower().startswith('darwin'):
        fonts_root = os.path.join(os.getenv('HOME'), 'Library',
                                  'Application Support',
                                  'Garmin', 'ConnectIQ', 'Fonts')
    os.makedirs(fonts_root, exist_ok=True)
    for font in get_font_list(token):
        font_filename = os.path.join(fonts_root, "%s.cft" % font['name'])
        md5_filename = os.path.join(fonts_root, "%s.md5" % font['name'])
        if os.path.exists(md5_filename):
            md5 = open(md5_filename).read().strip()
            if os.path.exists(font_filename) and md5 == font['fontHash']:
                continue
        open(md5_filename, "w").write(font['fontHash'])
        headers = {'authorization': 'Bearer %s' % token,
                   'accept': '*/*'}
        req = requests.get(
            APIGCS +
            "/ciq-product-onboarding/fonts/font?fontName=%s" % font['name'],
            headers=headers, verify=SSL_VERIFY)
        logger.info("Downloading font '%s'." % font['name'])
        open('%s.zip' % font_filename, "wb").write(req.content)
        zf = zipfile.ZipFile('%s.zip' % font_filename)
        zf.extractall(fonts_root)
        os.unlink('%s.zip' % font_filename)


def _install_devices(token):
    devices_root = os.path.join(os.getenv('HOME'), '.Garmin',
                                'ConnectIQ', 'Devices')
    if sys.platform.lower().startswith('darwin'):
        devices_root = os.path.join(os.getenv('HOME'), 'Library',
                                    'Application Support',
                                    'Garmin', 'ConnectIQ', 'Devices')
    os.makedirs(devices_root, exist_ok=True)
    for device in get_device_list(token):
        # {'deviceUuid': 'b957e0db-67bb-4b6f-9aa2-426efcbe46fe',
        # 'partNumber': '006-B2859-00',
        # 'name': 'descentmk1',
        # 'productInfoFileExists': True,
        # 'ciqInfoFileExists': True,
        # 'upcoming': False,
        # 'productInfoHash': 'c79e0b7fee6d01b0d47757cf7ad587e5',
        # 'ciqInfoHash': 'c96d495c2b8512a4e3c0c504d6f936a2',
        # 'group': 'Watches/Wearables',
        # 'displayName': 'Descent™ Mk1',
        # 'lastUpdateTime': '2020-08-19 17:16:16'}
        device_path = os.path.join(devices_root, device['name'])
        if not os.path.exists(device_path):
            headers = {'accept': '*/*',
                       'authorization': 'Bearer %s' % token}
            req = requests.get(
                APIGCS +
                "/ciq-product-onboarding/devices/%s/ciqInfo" %
                device['partNumber'],
                headers=headers, verify=SSL_VERIFY)
            logger.info("Downloading device '%s'." % device['name'])
            open(device_path + ".zip", "wb").write(req.content)
            zf = zipfile.ZipFile(device_path + ".zip")
            zf.extractall(device_path)
            os.unlink(device_path + ".zip")
