from setuptools import setup

console_scripts = """
ciqw-build = ciqw:build
ciqw-run = ciqw:run
ciqw-release = ciqw:release
ciqw-list-sdks = ciqw:list_sdks
ciqw-install-sdk = ciqw:install_sdk
ciqw-init = ciqw:init
ciqw-genkey = ciqw:genkey
ciqw-sim = ciqw:sim
"""

setup(name='ciqw',
      version='0.1.0',
      description="Connect IQ Wrapper",
      author="Jean Schurger",
      author_email='jean@schurger.org',
      packages=['ciqw'],
      entry_points={
          'console_scripts': console_scripts,
      },
      license='GPLv3')
