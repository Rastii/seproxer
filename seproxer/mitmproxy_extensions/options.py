import typing as t

import mitmproxy.options


class MitmproxyExtendedOptions(mitmproxy.options.Options):
    def __init__(self,
                 strip_headers: t.Optional[t.Iterable[t.Tuple[str, str]]]=None,
                 inject_js_error_detection: bool=True,
                 inject_js_error_detection_filter: str="~t text/html",
                 **kwargs) -> None:

        self.strip_headers = strip_headers or []
        self.inject_js_error_detection = inject_js_error_detection
        self.inject_js_error_detection_filter = inject_js_error_detection_filter

        super().__init__(**kwargs)
