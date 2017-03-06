"""
Extensions to mitmproxy master.
"""
import multiprocessing

from seproxer import mitmproxy_extensions
import seproxer.mitmproxy_extensions.addons

import mitmproxy.addons
import mitmproxy.master


class MasterProducer(mitmproxy.master.Master):
    def __init__(self, options, server,  # type: ignore
                 results_queue: multiprocessing.Queue,
                 push_event: multiprocessing.Event,
                 ) -> None:
        # Note: the above was set as type: ignore because mypy does not like multiprocessing.Event!
        super().__init__(options, server)
        # This addon will allow us to modify headers, this is particularly useful for appending
        # authentication cookies since selenium_extensions cannot modify HTTP ONLY cookies
        self.addons.add(mitmproxy.addons.setheaders.SetHeaders())
        # This add-on hooks into javascript window.onerror and all the console logging
        # methods to log message into our defined "window.__seproxer_logs" object
        self.addons.add(mitmproxy_extensions.addons.JSConsoleErrorInjection())
        # This addon will be responsible for storing our requests / responses in memory
        # and will allow us to push the results through out results_queue
        self.addons.add(mitmproxy_extensions.addons.MemoryStream())

        self.results_queue = results_queue
        self.push_event = push_event

    def tick(self, timeout):
        tick_result = super().tick(timeout)
        if self.push_event.is_set():
            ms = self.addons.get(seproxer.mitmproxy_extensions.addons.MemoryStream.get_class_name())

            # Get the flow results and restart by calling start again
            flow_results = ms.get_stream()
            ms.start()

            # Push the results to the result queue1
            self.results_queue.put(flow_results)
            self.push_event.clear()

        return tick_result
