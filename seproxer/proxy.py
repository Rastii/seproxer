import multiprocessing
import signal
import logging
import time
import typing as t  # NOQA

import seproxer.options
from seproxer import mitmproxy_extensions
import seproxer.mitmproxy_extensions.options
import seproxer.mitmproxy_extensions.master
from seproxer import seproxer_enums

import mitmproxy.proxy.config
import mitmproxy.proxy.server


logger = logging.getLogger(__name__)


class Error(Exception):
    """
    Generic module error
    """


class ProxyRunningError(Error):
    """
    Exception is raised when an operation assumes a proxy is not running
    and a proxy is indeed running
    """


class ProxyNotRunningError(Error):
    """
    Exception is raised when an operation is performed that requires
    the proxy to be running and the proxy is not running
    """


class ProxyProc(multiprocessing.Process):
    def __init__(self, proxy_master: mitmproxy_extensions.master.MasterProducer) -> None:
        super().__init__()
        self.proxy_master = proxy_master

    def _handle_sigint(self, signum, frame):
        _ = signum, frame  # NOQA
        self.proxy_master.shutdown()

    def run(self):
        signal.signal(signal.SIGTERM, self._handle_sigint)
        self.proxy_master.run()


class Runner:
    def __init__(self,
                 mitmproxy_options: mitmproxy_extensions.options.MitmproxyExtendedOptions) -> None:
        self.mitmproxy_options = mitmproxy_options
        # setup proxy server from options
        proxy_config = mitmproxy.proxy.config.ProxyConfig(mitmproxy_options)
        self._proxy_server = mitmproxy.proxy.server.ProxyServer(proxy_config)

        self._results_queue = multiprocessing.Queue()
        self._producer_push_event = multiprocessing.Event()  # type: ignore

        self._proxy_proc = None  # type: t.Optional[ProxyProc]

    def run(self):
        if self._proxy_proc:
            raise ProxyRunningError(
                "Cannot run proxy while proxy (pid: %s) is running", self._proxy_proc.pid)

        master_producer = mitmproxy_extensions.master.MasterProducer(
            options=self.mitmproxy_options,
            server=self._proxy_server,
            results_queue=self._results_queue,
            push_event=self._producer_push_event,
        )
        self._proxy_proc = ProxyProc(master_producer)
        self._proxy_proc.start()

    def done(self):
        if not self._proxy_proc:
            raise ProxyNotRunningError("Cannot end proxy when no proxy process is running")

        self._proxy_proc.terminate()
        self._proxy_proc.join()
        self._proxy_proc = None

    def get_results(self) -> bytes:
        if self._producer_push_event.is_set():
            logger.warning("Attempted to retrieve proxy results while proxy producer has not yet "
                           "cleared the push event")
            while not self._producer_push_event.is_set():
                time.sleep(0.1)

        self._producer_push_event.set()
        queue_result = self._results_queue.get()

        if queue_result:
            return queue_result.getvalue()

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "Runner":
        mitmproxy_options = mitmproxy_extensions.options.MitmproxyExtendedOptions(
            strip_headers=options.strip_headers,
            inject_js_error_detection=(
                options.selenium_webdriver_type is seproxer_enums.SeleniumBrowserTypes.FIREFOX
            ),
            keepserving=True,
            listen_port=options.mitmproxy_port,
            ssl_insecure=options.ignore_certificates,
            setheaders=options.set_headers,
        )
        return Runner(mitmproxy_options)