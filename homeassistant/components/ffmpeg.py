"""
Component that will help set the ffmpeg component.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/ffmpeg/
"""
import asyncio
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.util.async import run_coroutine_threadsafe

DOMAIN = 'ffmpeg'
REQUIREMENTS = ["ha-ffmpeg==0.15"]

_LOGGER = logging.getLogger(__name__)

DATA_BIN = 'ffmpeg_binary'
DATA_TEST = 'ffmpeg_test'

CONF_INPUT = 'input'
CONF_FFMPEG_BIN = 'ffmpeg_bin'
CONF_EXTRA_ARGUMENTS = 'extra_arguments'
CONF_OUTPUT = 'output'
CONF_RUN_TEST = 'run_test'

DEFAULT_BINARY = 'ffmpeg'
DEFAULT_RUN_TEST = True

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_FFMPEG_BIN, default=DEFAULT_BINARY): cv.string,
        vol.Optional(CONF_RUN_TEST, default=DEFAULT_RUN_TEST): cv.boolean,
    }),
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    """Setup the FFmpeg component."""
    domain_conf = config.get(DOMAIN, {})
    run_test = domain_conf.get(CONF_RUN_TEST, DEFAULT_RUN_TEST)

    hass.data[DATA_BIN] = domain_conf.get(CONF_FFMPEG_BIN, DEFAULT_BINARY)
    hass.data[DATA_TEST] = TestFfmpeg(hass, run_test)
    return True


class TestFfmpeg(object):
    """Handle Test/Checks inside Home-Assistant."""

    def __init__(self, hass, run_test=False):
        """Init Testclass."""
        self.hass = hass
        self._run_test = run_test
        self._cache = {}

    def run_test(self, input_source):
        """Run test on this input. TRUE is deactivate or run correct."""
        return run_coroutine_threadsafe(
            self.async_run_test(input_source), hass.loop).result()

    @asyncio.coroutine
    def async_run_test(self, input_source):
        """Run test on this input. TRUE is deactivate or run correct.

        This method must be run in the event loop.
        """
        from haffmpeg import TestAsync

        if self._run_test:
            # if in cache
            if input_source in self._cache:
                return self._cache[input_source]

            # run test
            ffmpeg_test = TestAsync(self.hass.data[DATA_BIN], loop=hass.loop)
            success = yield from ffmpeg_test.run_test(input_source)
            if not success:
                _LOGGER.error("FFmpeg '%s' test fails!", input_source)
                self._cache[input_source] = False
            else:
                self._cache[input_source] = True
            return self._cache[input_source]
        return True
