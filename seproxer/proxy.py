import multiprocessing
import signal
import logging
import time
import typing as t  # NOQA
import io
import ctypes

import seproxer.options
from seproxer import mitmproxy_extensions
import seproxer.mitmproxy_extensions.options
import seproxer.mitmproxy_extensions.master
from seproxer import seproxer_enums

import mitmproxy.proxy.config
import mitmproxy.proxy.server


logger = logging.getLogger(__name__)


class ProxyError(Exception):
    """
    Generic module error
    """


class ProxyRunningError(ProxyError):
    """
    Exception is raised when an operation assumes a proxy is not running
    and a proxy is indeed running
    """


class ProxyNotRunningError(ProxyError):
    """
    Exception is raised when an operation is performed that requires
    the proxy to be running and the proxy is not running
    """


class ProxyMalformedData(ProxyError):
    """
    Unexpected data was returned from the proxy
    """


class ProxyProc(multiprocessing.Process):
    def __init__(self, proxy_master: mitmproxy_extensions.master.ProxyMaster) -> None:
        super().__init__()
        self.proxy_master = proxy_master

    def _handle_sig(self, signum, frame):
        _ = signum, frame  # NOQA
        self.proxy_master.shutdown()

    def run(self):
        signal.signal(signal.SIGTERM, self._handle_sig)
        signal.signal(signal.SIGINT, self._handle_sig)
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
        self._has_active_flows_state = multiprocessing.Value(ctypes.c_bool, False)

        self._proxy_proc = None  # type: t.Optional[ProxyProc]

    def run(self):
        if self._proxy_proc:
            raise ProxyRunningError(
                "Cannot run proxy while proxy (pid: %s) is running", self._proxy_proc.pid)

        master_producer = mitmproxy_extensions.master.ProxyMaster(
            options=self.mitmproxy_options,
            server=self._proxy_server,
            results_queue=self._results_queue,
            push_event=self._producer_push_event,
            active_flows_state=self._has_active_flows_state,
        )
        self._proxy_proc = ProxyProc(master_producer)
        self._proxy_proc.start()

    @property
    def is_running(self) -> bool:
        """
        Indicates whether the proxy process is running
        """
        return bool(self._proxy_proc and self._proxy_proc.is_alive())

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
        queue_result = self._results_queue.get()  # type: t.Optional[io.BytesIO]

        if queue_result:
            if not isinstance(queue_result, io.BytesIO):
                logger.error(
                    "Expected BytesIO object, instead received {}".format(type(queue_result))
                )
                raise ProxyMalformedData("Unexpected data received from proxy")
            return queue_result.getvalue()

        return bytes()

    def has_pending_requests(self) -> bool:
        with self._has_active_flows_state.get_lock():  # type: ignore
            return self._has_active_flows_state.value  # type: ignore

    def clear_flows(self) -> None:
        """
        Removes any flows that have been stored in memory from the proxy
        """
        try:
            self.get_results()
        except ProxyError:
            return

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
