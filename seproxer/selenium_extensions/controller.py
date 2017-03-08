"""
This module contains the selenium master functionality that controls the selenium
web drivers.
"""
import typing as t
import logging

from seproxer.selenium_extensions import webdriver_factory
from seproxer.selenium_extensions import states
from seproxer.selenium_extensions import validators
import seproxer.selenium_extensions.states.managers
import seproxer.selenium_extensions.validators.managers
import seproxer.options

from selenium.webdriver.remote import webdriver as remote_webdriver
import selenium.common.exceptions as selenium_exceptions


logger = logging.getLogger(__name__)


class ControllerError(Exception):
    """
    Generic error related to a controller operation
    """


class ControllerResultsFailed(ConnectionError):
    """
    Exception occurred when a controller failed to to get results, typically caused by
    a webdriver error.
    """


class ControllerUrlResult:
    __slots__ = ("state_results", "validator_results")

    def __init__(self,
                 state_results: t.List[states.managers.StateResult],
                 validator_results: validators.PageValidatorResults) -> None:
        self.state_results = state_results
        self.validator_results = validator_results


class DriverController:
    """
    The purpose of this class is to drive the WebDriver and perform the
    appropriate validators on URLs once the defined state(s) are reached
    """
    def __init__(self,
                 driver: remote_webdriver.WebDriver,
                 loaded_state_manager: states.managers.LoadedStateManager,
                 validator_manager: validators.managers.PageValidatorManager) -> None:

        self._webdriver = driver
        self._loaded_state_manager = loaded_state_manager
        self._validator_manager = validator_manager

    def get_results(self, url: str) -> ControllerUrlResult:
        try:
            self._webdriver.get(url)
            # Wait until we can perform our validation
            state_results = self._loaded_state_manager.get_state_results(self._webdriver)
            # After our the page reaches a testable state, now let's run all our validators on it
            # TODO: Consider dependant graphs for validators based on states
            validator_results = self._validator_manager.validate(self._webdriver)
        except selenium_exceptions.WebDriverException as e:
            logging.exception("Failed result attempt for {}".format(url))
            raise ControllerResultsFailed(e)

        return ControllerUrlResult(state_results, validator_results)

    def done(self):
        self._webdriver.quit()

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "DriverController":
        driver = webdriver_factory.get_webdriver(options)
        loaded_state_manager = states.managers.LoadedStateManager.from_options(options)
        validator_manager = validators.managers.PageValidatorManager.from_options(options)

        return DriverController(
            driver=driver,
            loaded_state_manager=loaded_state_manager,
            validator_manager=validator_manager,
        )
