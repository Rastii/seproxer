import typing as t
import enum


class ResultLevel(enum.Enum):
    OK = 0
    WARNING = 1
    ERROR = 2

    def cascaded(self) -> t.Iterable["ResultLevel"]:
        if self is self.ERROR:
            return ResultLevel.ERROR,
        if self is self.WARNING:
            return ResultLevel.ERROR, ResultLevel.WARNING
        return ResultLevel.ERROR, ResultLevel.WARNING, ResultLevel.OK


class SeleniumBrowserTypes(enum.Enum):
    CHROME = 0
    PHANTOM_JS = 1
    FIREFOX = 2
