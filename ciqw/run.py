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
import subprocess
import xml.etree.ElementTree as ET
have_inotify = False
try:
    import inotify.adapters
    have_inotify = True
except Exception:
    pass 

from ciqw.sdks import _install_sdk
from ciqw.config import read_config, genkey


def _get_app_from_manifest():
    manifest = ET.parse('manifest.xml')
    ns = 'http://www.garmin.com/xml/connectiq'
    return manifest.find('{%s}application' % ns).attrib['entry']


def _get_sdk_bin(name, config):
    if not config.get('version'):
        _install_sdk()
    config.update(read_config())
    if sys.platform.lower().startswith('darwin'):
        if name == 'simulator':
            return os.path.join(os.getenv('HOME'), 'Library',
                                'Application Support',
                                'Garmin', 'ConnectIQ', 'Sdks',
                                'connectiq-sdk', 'bin', 'ConnectIQ.app',
                                'Contents', 'MacOS', 'simulator')            
        return os.path.join(os.getenv('HOME'), 'Library',
                            'Application Support',
                            'Garmin', 'ConnectIQ', 'Sdks',
                            'connectiq-sdk', 'bin', name)
        
        sdk = None
    for f in os.listdir(os.path.join(config['sdks'])):
        if (os.path.isdir(os.path.join(config['sdks'], f)) and
                f.startswith("connectiq-sdk-") and config['version'] in f):
            sdk = f
            break
    if sdk:
        return os.path.join(config['sdks'], sdk, 'bin', name)
    _install_sdk(config.get('version'))


def sim():
    config = read_config()
    command = _get_sdk_bin('simulator', config)
    print("Calling '%s'." % command)
    subprocess.Popen([command]).wait()


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
    if not have_inotify:
        print("Inotify not supported on your system yet.")
        sys.exit(1)
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
