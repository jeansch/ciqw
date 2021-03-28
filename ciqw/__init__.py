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


import os
import sys
import json
import stat
import configparser
import urllib.request
import zipfile
import subprocess
import inotify.adapters
import xml.etree.ElementTree as ET

DEVCIQ = 'https://developer.garmin.com/downloads/connect-iq/'

CONFIG_FILENAME = os.environ.get('CIQW_INI') or os.path.join(
    os.environ['HOME'], ".config", "ciqw", "config.ini")


DEFAULT_CONFIG = {
    'sdks': os.path.join(os.environ['HOME'],
                         ".Garmin", "ConnectIQ", "Sdks"),
    'sdkmanager': os.path.join(os.environ['HOME'],
                         ".Garmin", "ConnectIQ", "SdkManager"),
    'key': os.path.join(os.environ['HOME'], ".config", "ciqw", "key.der"),
    'device': 'fenix6',
    'flags': '--warn'}


def read_config():
    if not os.path.exists(CONFIG_FILENAME):
        init()
    cp = configparser.ConfigParser()
    cp.read(CONFIG_FILENAME)
    return dict(cp['ciqw'])


def init():
    if os.path.exists(CONFIG_FILENAME):
        print("Would not overwrite '%s'." % CONFIG_FILENAME)
        sys.exit(1)
    else:
        if not os.path.exists(os.path.dirname(CONFIG_FILENAME)):
            os.makedirs(os.path.dirname(CONFIG_FILENAME), exist_ok=True)
        cp = configparser.ConfigParser()
        cp['ciqw'] = DEFAULT_CONFIG
        with open(CONFIG_FILENAME, 'w') as configfile:
            cp.write(configfile)
        print("Created default config file: '%s'." % CONFIG_FILENAME)


def _get_app_from_manifest():
    manifest = ET.parse('manifest.xml')
    ns = 'http://www.garmin.com/xml/connectiq'
    return manifest.find('{%s}application' % ns).attrib['entry']


def _get_sdk_bin(name, config):
    if not config.get('version'):
        _install_sdk()
    config.update(read_config())
    sdk = None
    for f in os.listdir(os.path.join(config['sdks'])):
        if (os.path.isdir(os.path.join(config['sdks'], f)) and
            f.startswith("connectiq-sdk-") and config['version'] in f):
            sdk = f
            break
    if sdk:
        return os.path.join(config['sdks'], sdk, 'bin', name)
    _install_sdk(config.get('version'))



def _build(release=False):
    config = read_config()
    jungles = set()
    for f in os.listdir():
        if f.endswith('.jungle'):
            jungles.add(f)
    app = _get_app_from_manifest()
    command = [_get_sdk_bin('monkeyc', config)]
    if jungles:
        command.append('--jungles')
        command.extend(jungles)
    out = "%s.%s" % (app, "prg" if not release else "iq")
    if os.path.exists(out):
        print("Removing '%s'." % out)
        os.unlink(out)
    if not release:
        command.extend(['--device', config['device']])
    else:
        command.extend(['--release', '--package-app'])
    command.extend(['--output', out])
    command.extend(['--private-key', config['key']])
    if not os.path.exists(config['key']):
        genkey()
    command.extend(config.get('flags', '').split())
    print("Calling '%s'." % " ".join(command))
    subprocess.Popen(command).wait()
    if os.path.exists(out):
        print("Generated '%s'." % os.path.abspath(out))


def _run(force_build=False):
    config = read_config()
    app = _get_app_from_manifest()
    out = "%s.prg" % app
    if force_build or not os.path.exists(out):
        _build()
    os.environ['JAVA_OPTIONS'] = "--add-modules=java.xml.bind"
    command = [_get_sdk_bin('monkeydo', config),
               out, config['device']]
    print("Calling '%s'." % " ".join(command))
    subprocess.Popen(command).wait()



# TODO check for 42877 port to see if simulator is here

def _may_build_and_run(path, filename):
    print("File modified: '%s'." % os.path.join(path, filename))
    out = "%s.prg" % _get_app_from_manifest()
    if not os.path.exists(out):
        _run(force_build=True)
    if os.stat(os.path.join(path, filename)).st_mtime > os.stat(out).st_mtime:
        _run(force_build=True)


def _auto():
    i = inotify.adapters.InotifyTree(".")
    for _ev, op, path, filename in i.event_gen(yield_nones=False):
        if 'IN_CLOSE_WRITE' in op:
            # check if in resources, sources
            # and for filename (.jungle. .xml)
            # Rebuild if necessary
            # check stat of file and prg file
            if any((
                    filename == 'manifest.xml',
                    path == '.' and filename.endswith('.monkey'),
                    path.startswith('./source') and filename.endswith('.mc'),
                    path.startswith('./resources') and
                    filename.endswith('.xml') and
                    not filename.endswith('.debug.xml'),
                    path.startswith('./resources') and
                    filename.endswith('.png'))):
                _may_build_and_run(path, filename)

def sim():
    config = read_config()
    command = _get_sdk_bin('simulator', config)
    print("Calling '%s'." % command)
    subprocess.Popen([command]).wait()


def _cd_call(fct):
    try:
        cwd = None
        path = sys.argv[1] if len(sys.argv) == 2 else None
        if path:
            cwd = os.path.abspath(os.getcwd())
            os.chdir(path)
        fct()
        if path:
            os.chdir(cwd)
    except Exception as e:
        print(str(e))
        sys.exit(1)


def build():
    _cd_call(_build)


def run():
    _cd_call(_run)


def auto():
    _cd_call(_auto)


def release():
    _build(release=True)


def _install_sdk(version=None):
    sdks = get_available_sdks()
    if not version:
        version = [v for v in sdks if 'preview' not in v][-1]
    if version not in sdks:
        raise Exception("Version '%s' is not available." % version)
    config = read_config()
    target = os.path.join(config['sdks'],
                          ".".join(sdks[version]['package'].split(".")[:-1]))
    os.makedirs(target, exist_ok=True)
    package_name = sdks[version]['package']
    package = os.path.join(config.get('sdks'), package_name)
    if not os.path.exists(package):
        url = DEVCIQ + 'sdks/' + sdks[version]['package']
        print("Downloading '%s'" % url)
        open(package, "wb").write(
            urllib.request.urlopen(url).read())
    if not os.path.exists(os.path.join(target, 'bin', 'monkeyc')):
        print("Extracting '%s' to '%s'." % (package, target))
        zf = zipfile.ZipFile(package)
        zf.extractall(target)
    if config.get('version') != version:
        print("Updating version configuration with '%s'." % version)
        config['version'] = version
        cp = configparser.ConfigParser()
        cp['ciqw'] = config
        with open(CONFIG_FILENAME, 'w') as configfile:
            cp.write(configfile)
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
    sdkmanager = json.loads(urllib.request.urlopen(
        DEVCIQ + 'sdk-manager/' + 'sdk-manager.json').read())
    archive = sdkmanager[package]
    config = read_config()
    if not os.path.exists(config['sdkmanager']):
        os.makedirs(config['sdkmanager'], exist_ok=True)
    archive_file = os.path.join(config['sdkmanager'],
                                '%s-%s.zip' % (archive.replace(".zip", ""),
                                               sdkmanager['version']))

    if not os.path.exists(archive_file):
        url = DEVCIQ + 'sdk-manager/' + archive
        print("Downloading '%s'" % url)
        open(archive_file, "wb").write(
            urllib.request.urlopen(url).read())
    bin = os.path.join(config['sdkmanager'], 'bin', 'sdkmanager')
    if not os.path.exists(bin):
        print("Extracting '%s' to '%s'." % (archive_file, config['sdkmanager']))
        zf = zipfile.ZipFile(archive_file)
        zf.extractall(config['sdkmanager'])
        os.chmod(bin, os.stat(bin).st_mode | stat.S_IEXEC)


def run_sdkmanager():
    config = read_config()
    if not os.path.exists(os.path.join(config['sdkmanager'], 'bin', 'sdkmanager')):
        install_sdkmanager()
    subprocess.Popen([os.path.join(
        config['sdkmanager'], 'bin', 'sdkmanager')]).wait()


def install_sdk():
    try:
        _install_sdk(sys.argv[1] if len(sys.argv) == 2 else None)
    except Exception as e:
        print(str(e))
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
    for sdk in json.loads(urllib.request.urlopen(
            DEVCIQ + 'sdks/' + 'sdks.json').read()):
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
        print(str(e))
        sys.exit(1)
    for version, sdk in sdks.items():
        print("- %s: '%s' (release: %s)" % (
            version, sdk['title'], sdk['release']))



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
