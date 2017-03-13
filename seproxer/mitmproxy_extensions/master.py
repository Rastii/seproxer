"""
Extensions to mitmproxy master.
"""
import multiprocessing

from seproxer import mitmproxy_extensions
import seproxer.mitmproxy_extensions.addons  # NOQA
import seproxer.mitmproxy_extensions.options

import mitmproxy.addons
import mitmproxy.proxy.server
import mitmproxy.master


class ProxyMaster(mitmproxy.master.Master):
    """
    Implements mitmproxy master to produce flows through a shared Queue and a shared
    state attribute that specifies if there are any responses pending
    """
    def __init__(self,  # type: ignore # (mypy doesn't like multiprocessing lib)
                 options: seproxer.mitmproxy_extensions.options,
                 server: mitmproxy.proxy.server,
                 results_queue: multiprocessing.Queue,
                 push_event: multiprocessing.Event,
                 active_flows_state: multiprocessing.Value,
                 ) -> None:
        """
        :param options: The extended mitmproxy options, used to configure our addons
        :param server: The mitmproxy server that the proxy will be interfacing with
        :param results_queue: The mitmproxy flows will be pushed into this queue
        :param push_event: When this event is set, the stored flows will
                           be pushed into the `results_queue`
        :param active_flows_state: A shared state that determines if there are any active flows,
                                   that is, if any requests have pending responses
        """
        super().__init__(options, server)
        # This addon will allow us to modify headers, this is particularly useful for appending
        # authentication cookies since selenium_extensions cannot modify HTTP ONLY cookies
        self.addons.add(mitmproxy.addons.setheaders.SetHeaders())
        # This add-on hooks into javascript window.onerror and all the console logging
        # methods to log message into our defined "window.__seproxer_logs" object
        self.addons.add(mitmproxy_extensions.addons.JSConsoleErrorInjection())
        # This addon will be responsible for storing our requests / responses in memory
        # and will allow us to push the results through out results_queue
        self._memory_stream_addon = mitmproxy_extensions.addons.MemoryStream()
        self.addons.add(self._memory_stream_addon)

        self.results_queue = results_queue
        self.push_event = push_event
        self.active_flows_state = active_flows_state

    def tick(self, timeout):
        """
        Extends the Master's tick method to update our active flows state and to push
        our results into the results queue if the push_event is set
        """
        tick_result = super().tick(timeout)

        # Update our active flow state
        has_active_flows = self._memory_stream_addon.has_active_flows()
        if has_active_flows != self.active_flows_state.value:
            with self.active_flows_state.get_lock():
                self.active_flows_state.value = has_active_flows

        if self.push_event.is_set():
            # Get the flow results and restart by calling start again
            flow_results = self._memory_stream_addon.get_stream()
            self._memory_stream_addon.start()

            # Push the results to the result queue1
            self.results_queue.put(flow_results)
            self.push_event.clear()

        return tick_result
