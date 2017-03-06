import abc
import time

from seproxer.selenium_extensions import states
from selenium.webdriver.remote import webdriver


class LoadedStateHandler(metaclass=abc.ABCMeta):
    """
    This is an abstract class for defining that a given web driver
    is on a page that is in a loaded state.
    """
    def __init__(self, timeout: int=0) -> None:
        self._timeout = timeout

    @classmethod
    def class_name(cls):
        return cls.__name__.lower()

    def name(self):
        return self.class_name()

    @abc.abstractmethod
    def is_state_supported(self, driver: webdriver):
        """
        Is the page that the driver is currently on supported for this state handler?

        For example, if we have an Angular loaded state object, we must first ensure
        that angular exists....

        Alternatively, native javascript executions might not need this and can
        simply return True for all cases.
        """

    @abc.abstractmethod
    def check(self, driver: webdriver):
        """
        This method should return a boolean to indicate whether or not the driver
        is in the state expected for the implemented state handler.
        """

    def block_until_state(self, driver):
        """
        Will continue in a blocking loop until the driver reaches the expected state
        or the time exceeds the specified timeout.

        :param driver: The Selenium WebDriver object that needs its' state verified.
        """
        start_time = time.time() if self._timeout else None

        # TODO: When more states get implemented, it would probably be a good idea to make this
        # an async coroutine so we can sleep and let another state validator have a go!
        while not self.check(driver):
            time.sleep(0.2)

            if start_time and (time.time() - start_time) >= self._timeout:
                raise states.StateNotReached("Timed out while waiting for state to be reached")
