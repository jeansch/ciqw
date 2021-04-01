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
import stat
import zipfile
import subprocess
import configparser
import shutil
import requests
from ciqw.config import read_config, CONFIG_FILENAME

logger = logging.getLogger(__name__)

DEVCIQ = 'https://developer.garmin.com/downloads/connect-iq/'
SSL_VERIFY = not sys.platform.lower().startswith('darwin')


def _install_sdk(version=None):
    sdks = get_available_sdks()
    if not version:
        version = [v for v in sdks if 'preview' not in v][-1]
    if version not in sdks:
        raise Exception("Version '%s' is not available." % version)
    config = read_config()
    target = os.path.join(config['sdks'],
                          ".".join(sdks[version]['package'].split(".")[:-1]))
    package_basename = os.path.basename(target)
    if sys.platform.lower().startswith('darwin'):
        target = os.path.join(config['sdks'], "connectiq-sdk")
    package_name = sdks[version]['package']
    package = os.path.join(config.get('sdks'), package_name)
    if not os.path.exists(package):
        url = DEVCIQ + 'sdks/' + sdks[version]['package']
        logger.info("Downloading '%s'" % url)
        os.makedirs(os.path.dirname(target), exist_ok=True)
        open(package, "wb").write(
            requests.get(url, verify=SSL_VERIFY).content)
    if package.endswith(".zip"):
        if not os.path.exists(os.path.join(target, 'bin', 'monkeyc')):
            logger.info("Extracting '%s' to '%s'." % (package, target))
            os.makedirs(target, exist_ok=True)
            zf = zipfile.ZipFile(package)
            zf.extractall(target)
    if package.endswith(".dmg"):
        if not os.path.exists(os.path.join(target, 'bin', 'monkeyc')):
            logger.info("Extracting '%s' to '%s'." % (package, target))
            VOL = "/Volumes/Connect IQ SDK/"
            subprocess.Popen(["hdiutil", "mount", package]).wait()
            shutil.copytree(os.path.join(VOL, package_basename), target)
            subprocess.Popen(["hdiutil", "unmount", VOL]).wait()
    if config.get('version') != version:
        logger.info("Updating version configuration with '%s'." % version)
        config['version'] = version
        cp = configparser.ConfigParser()
        cp['ciqw'] = config
        with open(CONFIG_FILENAME, 'w') as configfile:
            cp.write(configfile)
    if os.path.exists(os.path.join(target, 'bin')):
        for f in os.listdir(os.path.join(target, 'bin')):
            bin = os.path.join(target, 'bin', f)
            os.chmod(bin, os.stat(bin).st_mode | stat.S_IEXEC)


def install_sdkmanager():
    packages = {'linux': 'linux',
                'windows': 'windows',
                'darwin': 'mac'}
    package = None
    for _os, _package in packages.items():
        if sys.platform.lower().startswith(_os):
            package = _package
    if not package:
        raise Exception("Unable to find package of your OS: '%s'" %
                        sys.platform)
    sdkmanager = requests.get(
        DEVCIQ + 'sdk-manager/' + 'sdk-manager.json',
        verify=SSL_VERIFY).json()
    archive = sdkmanager[package]
    config = read_config()
    if not os.path.exists(config['sdkmanager']):
        os.makedirs(config['sdkmanager'], exist_ok=True)
    ext = archive.split(".")[-1]
    archive_file = os.path.join(
        config['sdkmanager'],
        '%s-%s.%s' % (archive.replace(".%s" % ext, ""),
                      sdkmanager['version'], ext))
    if not os.path.exists(archive_file):
        url = DEVCIQ + 'sdk-manager/' + archive
        logger.info("Downloading '%s'" % url)
        open(archive_file, "wb").write(requests.get(
            url, verify=SSL_VERIFY).content)
    bin = os.path.join(config['sdkmanager'], 'bin', 'sdkmanager')
    if sys.platform.lower().startswith('darwin'):
        bin = os.path.join(config['sdkmanager'], 'SdkManager.app',
                           'Contents', 'MacOS', 'sdkmanager')
    if not os.path.exists(bin):
        if ext == 'zip':
            logger.info("Extracting '%s' to '%s'." % (archive_file,
                                                config['sdkmanager']))
            zf = zipfile.ZipFile(archive_file)
            zf.extractall(config['sdkmanager'])
            os.chmod(bin, os.stat(bin).st_mode | stat.S_IEXEC)
        if ext == 'dmg':
            logger.info("Extracting '%s' to '%s'." % (
                archive_file, config['sdkmanager']))
            VOL = "/Volumes/Connect IQ SDK Manager/"
            subprocess.Popen(["hdiutil", "mount", archive_file]).wait()
            shutil.copytree(os.path.join(os.path.join(VOL, 'SdkManager.app')),
                            os.path.join(config['sdkmanager'],
                                         'SdkManager.app'))
            subprocess.Popen(["hdiutil", "unmount", VOL]).wait()


def run_sdkmanager():
    config = read_config()
    bin = os.path.join('bin', 'sdkmanager')
    if sys.platform.lower().startswith('darwin'):
        bin = os.path.join('SdkManager.app', 'Contents',
                           'MacOS', 'sdkmanager')
    fqbin = os.path.join(config['sdkmanager'], bin)
    if not os.path.exists(fqbin):
        install_sdkmanager()
    subprocess.Popen([fqbin]).wait()


def install_sdk():
    try:
        _install_sdk(sys.argv[1] if len(sys.argv) == 2 else None)
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)


def get_available_sdks():
    sdks = {}
    packages = {'linux': 'linux',
                'windows': 'windows',
                'darwin': 'mac'}
    package = None
    for _os, _package in packages.items():
        if sys.platform.lower().startswith(_os):
            package = _package
    if not package:
        raise Exception("Unable to find package of your OS: '%s'" %
                        sys.platform)
    for sdk in requests.get(DEVCIQ + 'sdks/' + 'sdks.json',
                            verify=SSL_VERIFY).json():
        package_name = sdk.get(package)
        if package_name:
            sdks[sdk['version']] = {'title': sdk['title'],
                                    'release': sdk['release'],
                                    'package': package_name}
    return sdks


def list_sdks():
    try:
        sdks = get_available_sdks()
    except Exception as e:
        logger.error(str(e))
        sys.exit(1)
    for version, sdk in sdks.items():
        logger.info("- %s: '%s' (release: %s)" % (
            version, sdk['title'], sdk['release']))
