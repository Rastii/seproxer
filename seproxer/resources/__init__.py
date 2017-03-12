import pkg_resources


SEPROXER_PACKAGE_NAME = "seproxer"
JAVASCRIPT_DATA_DIR = "javascript"


def get_javascript_resource(resource_path):
    name = "{}/{}".format(JAVASCRIPT_DATA_DIR, resource_path)
    with pkg_resources.resource_stream(SEPROXER_PACKAGE_NAME, name) as f:
        return f.read()


class JavascriptResource:
    __slots__ = ("_name", "_javascript")

    def __init__(self, name: str, javascript: bytes):
        self._name = name
        # We expect to read bytes using the pkg_resource so this will properly convert it
        # into a valid utf-8 sting for JS
        self._javascript = javascript.decode("utf-8")

    @property
    def name(self) -> str:
        return self._name

    @property
    def javascript(self) -> str:
        return self._javascript
