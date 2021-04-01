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

from setuptools import setup

console_scripts = """
ciqw-build = ciqw:build
ciqw-auto = ciqw:auto
ciqw-run = ciqw:run
ciqw-release = ciqw:release
ciqw-list-sdks = ciqw:list_sdks
ciqw-install-sdk = ciqw:install_sdk
ciqw-install-sdkmanager = ciqw:install_sdkmanager
ciqw-run-sdkmanager = ciqw:run_sdkmanager
ciqw-init = ciqw:init
ciqw-genkey = ciqw:genkey
ciqw-sim = ciqw:sim
ciqw-login = ciqw:login
ciqw-install-fonts-and-devices = ciqw:install_fonts_and_devices
"""

setup(name='ciqw',
      version='0.4.7',
      description="Connect IQ Wrapper",
      author="Jean Schurger",
      author_email='jean@schurger.org',
      packages=['ciqw'],
      entry_points={
          'console_scripts': console_scripts,
      },
      install_requires=['inotify', 'requests', 'pyquery'],
      license='GPLv3')
