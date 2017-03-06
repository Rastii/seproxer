import typing as t
import logging

import seproxer.options

from seproxer.selenium_extensions import states
import seproxer.selenium_extensions.states.base
import seproxer.selenium_extensions.states.angular


logger = logging.getLogger(__name__)


class StateResult:
    def __init__(self, name: str, is_supported: bool, is_state_reached: bool) -> None:
        self.name = name
        self.is_supported = is_supported
        self.is_state_reached = is_state_reached


class LoadedStateManager:
    def __init__(self, initial_states: t.Iterable[states.base.LoadedStateHandler]=None,
                 timeout_time: int=0) -> None:
        if initial_states is None:
            initial_states = []
        self._states = {s.name(): s for s in initial_states}
        self._timeout_time = timeout_time

    def add_state(self, state: states.base.LoadedStateHandler):
        self._states[state.name()] = state

    def get_state(self, name: str):
        return self._states.get(name)

    def block_until_all_states_reached(self, driver) -> t.List[StateResult]:
        """
        Blocks until all the states in the state manager reaches their expected states.
        """
        state_results = []
        for state in self._states.values():
            is_supported = False
            is_reached = False
            if state.is_state_supported(driver):
                is_supported = True
                try:
                    state.block_until_state(driver)
                    is_reached = True
                except states.StateNotReached:
                    pass
            else:
                logger.debug(
                    "Ignored LoadedState %s checker, not supported for URL: %s",
                    state.name(),
                    driver.current_url,
                )
            state_results.append(StateResult(
                name=state.name(),
                is_supported=is_supported,
                is_state_reached=is_reached,
            ))
        return state_results

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "LoadedStateManager":
        initial_states = []
        if options.check_angular_app:
            initial_states.append(states.angular.AngularLoadedState())

        return LoadedStateManager(initial_states=initial_states)
