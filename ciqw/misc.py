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
import subprocess

from ciqw.config import read_config, genkey  # pylint: disable=C0413
from ciqw.run import get_sdk_root


logger = logging.getLogger(__name__)


def doc():
    config = read_config()
    command = ['xdg-open', os.path.join(get_sdk_root(
        'monkeydo', config), 'README.html')]
    logger.info("Calling '%s'." % " ".join(command))
    p = subprocess.Popen(command)


def samples():
    config = read_config()
    command = ['xdg-open', os.path.join(get_sdk_root(
        'monkeydo', config), 'samples')]
    logger.info("Calling '%s'." % " ".join(command))
    p = subprocess.Popen(command)


def samples_path():
    config = read_config()
    print(os.path.join(get_sdk_root(
        'monkeydo', config), 'samples'))
