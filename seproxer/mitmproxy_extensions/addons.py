"""
This module contains custom mitmproxy addons.
"""
import io
import bs4

from seproxer import resources
import seproxer.resources.injectable_js  # NOQA

import mitmproxy.io
import mitmproxy.exceptions
from mitmproxy import flowfilter

import mitmproxy.http


class MemoryStream:
    """
    A similar concept to `mitmproxy.addons.streamfile` but instead of writing to a file
    it writes to an in memory ByteIO object essentially storing flows in memory.
    """
    def __init__(self):
        self.stream = None
        self.active_flows = None
        self.strip_headers_list = []

    @classmethod
    def get_class_name(cls):
        return cls.__name__.lower()

    def configure(self, options, updated):
        if "strip_headers" in updated:
            self.strip_headers_list = []
            for flow_pattern, header in options.strip_headers:
                flow_filter = flowfilter.parse(flow_pattern)
                if not flow_filter:
                    raise mitmproxy.exceptions.OptionsError(
                        "Invalid strip_headers filter pattern {}".format(flow_pattern))

                self.strip_headers_list.append((flow_filter, header))

    def process_flow(self, flow):
        # If we have a strip headers list, let's remove all headers that match!
        for flow_filter, header in self.strip_headers_list:
            if flow_filter(flow):
                flow.request.headers.pop(header, None)

    def tcp_start(self, flow):
        if self.stream:
            self.active_flows.add(flow)

    def tcp_end(self, flow):
        if self.stream:
            self.stream.add(flow)
            self.active_flows.discard(flow)

    def response(self, flow):
        if self.stream:
            self.process_flow(flow)
            self.stream.add(flow)
            self.active_flows.discard(flow)

    def request(self, flow):
        if self.stream:
            self.active_flows.add(flow)

    def start(self):
        self.stream = mitmproxy.io.FlowWriter(io.BytesIO())
        self.active_flows = set()

    def get_stream(self):
        # Add any remaining flows in the active flows
        for flow in self.active_flows:
            self.process_flow(flow)
            self.stream.add(flow)

        return self.stream.fo


class JSConsoleErrorInjection:
    """
    Injects javascript into HTML pages to handle error events and store them
    globally, that is, within the window context.

    This is particularly useful for browsers that don't support browser log retrieval,
    such as Firefox.  Can't blame though, w3c webdriver spec does not specify that it
    is required :-(
    """
    def __init__(self):
        self._filter = None

    def configure(self, options, updated):
        if "inject_js_error_detection" in updated and options.inject_js_error_detection:
            pattern = options.inject_js_error_detection_filter
            self._filter = flowfilter.parse(pattern)
            if not self._filter:
                raise mitmproxy.exceptions.OptionsError(
                    "Invalid inject_js_error_detection_filter pattern {}".format(pattern)
                )

    def response(self, flow: mitmproxy.http.HTTPFlow):
        if flow.response.status_code != 200 or not self._filter or not self._filter(flow):
            return

        bs_html = bs4.BeautifulSoup(flow.response.content, "html.parser")
        if not bs_html.head:
            return

        injected_script = bs_html.new_tag(
            name="script",
            type="application/javascript",
        )
        injected_script.string = resources.injectable_js.console_error_detection.javascript
        bs_html.head.insert(0, injected_script)

        flow.response.content = bs_html.encode()
