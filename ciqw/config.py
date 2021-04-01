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
import logging.config
import os
import sys
import subprocess
import configparser

logger = logging.getLogger(__name__)

CONFIG_FILENAME = os.environ.get('CIQW_INI') or os.path.join(
    os.environ['HOME'], ".config", "ciqw", "config.ini")


DEFAULT_CONFIG = {
    'key': os.path.join(os.environ['HOME'], ".config", "ciqw", "key.der"),
    'device': 'fenix6',
    'flags': '--warn'}

if sys.platform.lower().startswith('darwin'):
    DEFAULT_CONFIG.update({
        'sdks': os.path.join(os.environ['HOME'],
                             'Library',
                             'Application Support',
                             'Garmin',
                             "ConnectIQ", "Sdks"),
        'sdkmanager': os.path.join(os.environ['HOME'],
                                   'Library',
                                   'Application Support',
                                   'Garmin',
                                   "ConnectIQ", "SdkManager"),
    })
else:
    DEFAULT_CONFIG.update({
        'sdks': os.path.join(os.environ['HOME'],
                             ".Garmin", "ConnectIQ", "Sdks"),
        'sdkmanager': os.path.join(os.environ['HOME'],
                                   ".Garmin", "ConnectIQ", "SdkManager"),
    })


def read_config():
    if not os.path.exists(CONFIG_FILENAME):
        init()
    cp = configparser.ConfigParser()
    cp.read(CONFIG_FILENAME)
    return dict(cp['ciqw'])


def init():
    if os.path.exists(CONFIG_FILENAME):
        logger.error("Would not overwrite '%s'." % CONFIG_FILENAME)
        sys.exit(1)
    else:
        if not os.path.exists(os.path.dirname(CONFIG_FILENAME)):
            os.makedirs(os.path.dirname(CONFIG_FILENAME), exist_ok=True)
        cp = configparser.ConfigParser()
        cp['ciqw'] = DEFAULT_CONFIG
        with open(CONFIG_FILENAME, 'w') as configfile:
            cp.write(configfile)
        logger.info("Created default config file: '%s'." % CONFIG_FILENAME)


def setup_logger():
    # [loggers]
    # keys = root, ciqw, urllib3

    # [logger_root]
    # handlers =

    # [logger_ciqw]
    # level = DEBUG
    # handlers = console
    # qualname = ciqw

    # [logger_urllib3]
    # level = DEBUG
    # handlers = console
    # qualname = urllib3

    # [handlers]
    # keys = console

    # [formatters]
    # keys = generic

    # [formatter_generic]

    # [handler_console]
    # class = StreamHandler
    # args = (sys.stderr,)

    if os.path.exists(CONFIG_FILENAME):
        try:
            logging.config.fileConfig(CONFIG_FILENAME)
        except Exception:
            pass


def _genkey(der):
    pem = der.replace('.der', '.pem')
    subprocess.Popen(["openssl", "genrsa", "-out", pem, "4096"],
                     stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL).wait()
    subprocess.Popen(["openssl", "pkcs8", "-topk8", "-inform", "PEM",
                      "-outform", "DER",
                      "-in", pem,
                      "-out", der, "-nocrypt"]).wait()


def genkey():
    _genkey(sys.argv[1] if len(sys.argv) == 2 else
            read_config()['key'])
