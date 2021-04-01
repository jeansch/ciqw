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
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logging.getLogger().handlers[0].setFormatter(
    logging.Formatter('%(message)s'))

from ciqw.sdks import  install_sdk, install_sdkmanager, list_sdks, run_sdkmanager
from ciqw.config import init, setup_logger
from ciqw.run import build, run, auto, sim, release
from ciqw.auth import login
from ciqw.fonts_and_devices import install_fonts_and_devices

setup_logger()
