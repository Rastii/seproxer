import pkg_resources


SEPROXER_PACKAGE_NAME = "seproxer"
JAVASCRIPT_DATA_DIR = "javascript"


class JavascriptResource:
    __slots__ = ("_name", "_javascript")

    def __init__(self, name: str, javascript: str) -> None:
        self._name = name
        self._javascript = javascript

    @property
    def name(self) -> str:
        return self._name

    @property
    def javascript(self) -> str:
        return self._javascript


def get_javascript_resource(name: str, resource_path: str) -> JavascriptResource:
    file_path = "{}/{}".format(JAVASCRIPT_DATA_DIR, resource_path)
    with pkg_resources.resource_stream(SEPROXER_PACKAGE_NAME, file_path) as f:
        javascript = f.read()

    return JavascriptResource(
        name=name,
        javascript=javascript.decode("utf-8"),
    )
