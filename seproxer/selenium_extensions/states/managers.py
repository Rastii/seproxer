import typing as t
import logging

import seproxer.options

from seproxer.selenium_extensions import states
import seproxer.selenium_extensions.states.base
import seproxer.selenium_extensions.states.angular

from selenium.webdriver.remote import webdriver


logger = logging.getLogger(__name__)


class StateResult:
    def __init__(self, name: str, is_supported: bool, is_state_reached: bool) -> None:
        self.name = name
        self.is_supported = is_supported
        self.is_state_reached = is_state_reached


class LoadedStateManager:
    def __init__(self,
                 state_auditors: t.Iterable[states.base.LoadedStateHandler]=None,
                 timeout_time: int=0
                 ) -> None:
        if state_auditors is None:
            state_auditors = []
        self._state_auditors = {s.name(): s for s in state_auditors}
        self._timeout_time = timeout_time

    def get_state_results(self, driver: webdriver) -> t.List[StateResult]:
        """
        Returns a list of StateResults that are produced by auditing the contents
        and/or javascript execution of a web page using the webdriver.

        Note that when auditing a given web page it may take some time to reach a
        desired state.  For example, if we have determined that a web page performs
        additional network requests, in order for the state to be fulfilled, it must
        wait for all the network requests to be resolved.
        """
        state_results = []
        for state in self._state_auditors.values():
            is_supported = False
            is_reached = False
            if state.is_state_supported(driver):
                is_supported = True
                try:
                    is_reached = state.block_until_state(driver)
                except states.StateNotReached:
                    pass
            else:
                logger.debug(
                    "Ignored LoadedState %s checker, not supported for URL: %s",
                    state.name(),
                    driver.current_url,
                )
            state_results.append(
                StateResult(state.name(), is_supported, is_reached)
            )
        return state_results

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "LoadedStateManager":
        state_auditors = []
        if options.check_angular_app:
            state_auditors.append(states.angular.AngularLoadedState())

        return LoadedStateManager(state_auditors=state_auditors)
