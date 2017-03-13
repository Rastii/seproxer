import typing as t
import uuid
import logging

import seproxer.selenium_extensions.states.managers
import seproxer.selenium_extensions.validators.managers

from seproxer.selenium_extensions import controller

import seproxer.handlers
import seproxer.proxy

import seproxer.options

logger = logging.getLogger(__name__)


class Error(Exception):
    """
    Generic module level error
    """


class SeproxerUrlResult:
    __slots__ = (
        "url", "status_code", "state_results", "validator_results", "proxy_results", "uuid",
    )

    def __init__(self, url, driver_results, proxy_results):
        self.url = url
        self.state_results = driver_results.state_results
        self.validator_results = driver_results.validator_results
        self.proxy_results = proxy_results

        self.status_code = self.validator_results.overall_status()

        self.uuid = str(uuid.uuid4())


class ProxyWaitForPendingRequests(controller.ControllerWait):
    """
    Class implements a wait that waits for all network requests to be fulfilled.
    """
    # TODO: Implement option for timeout!
    def __init__(self, proxy: seproxer.proxy.Runner) -> None:
        self._proxy = proxy
        super().__init__()

    def check(self) -> bool:
        return not self._proxy.has_pending_requests()


class Seproxer:
    def __init__(self,
                 driver_controller: controller.DriverController,
                 proxy: seproxer.proxy.Runner,
                 result_handler: seproxer.handlers.ResultHandlerManager) -> None:
        self._driver_controller = driver_controller
        self._proxy = proxy
        self._result_handler = result_handler

        # TODO: Make this an option
        self._proxy_pending_requests_wait = ProxyWaitForPendingRequests(proxy)
        self._proxy.run()

    def test_urls(self, urls: t.Iterable[str]):
        self._proxy.clear_flows()
        for url in urls:
            # TODO: Handle both of these failing
            driver_results = self._driver_controller.get_results(
                url=url,
                controller_wait=self._proxy_pending_requests_wait,
            )
            proxy_results = self._proxy.get_results()

            result = SeproxerUrlResult(
                url=url,
                driver_results=driver_results,
                proxy_results=proxy_results,
            )
            self._result_handler.handle(result)

    def done(self):
        if self._proxy.is_running:
            self._proxy.done()
        self._result_handler.done()
        self._driver_controller.done()

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "Seproxer":
        proxy = seproxer.proxy.Runner.from_options(options)
        driver_controller = controller.DriverController.from_options(options)
        result_handler = seproxer.handlers.ResultHandlerManager.from_options(options)

        return Seproxer(
            driver_controller=driver_controller,
            proxy=proxy,
            result_handler=result_handler,
        )
