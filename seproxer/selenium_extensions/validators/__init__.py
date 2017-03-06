import abc
import json
import typing as t
import logging

from seproxer import seproxer_enums

import selenium.webdriver.remote.webdriver


logger = logging.Logger(__name__)


class Error(Exception):
    """
    Generic module level exception
    """


class Result:
    __slots__ = ("name", "status", "message", "data")

    def __init__(self, name: str, status: seproxer_enums.ResultLevel, message: str=None,
                 data: t.Optional[t.Any]=None,
                 ) -> None:
        """
        :param name: The validator name
        :param status: The status of the result, which can be either of the following:
        :param message: A general message about the validation -- mostly used for warnings/errors.
        :param data: Any sort of data structure that will be dumped with the message.  Typically
            used for warnings/errors and should remain JSON serializable.
        """
        self.name = name
        self.status = status
        self.message = message

        if data:
            # Assert here because if this fails it is most likely due to programmer error
            assert json.dumps(data)
        self.data = data

    def as_dict(self):
        return {
            "type": self.name,
            "message": self.message,
            "data": self.data,
        }


class PageValidatorResults:
    """
    Used to hold a collection of results
    """
    def __init__(self,
                 ok: t.Optional[t.List[Result]]=None,
                 warning: t.Optional[t.List[Result]]=None,
                 error: t.Optional[t.List[Result]]=None,
                 ) -> None:

        self._ok = ok or []
        self._warning = warning or []
        self._error = error or []

    def append(self, result: Result):
        if result.status is seproxer_enums.ResultLevel.OK:
            self._ok.append(result)
        elif result.status is seproxer_enums.ResultLevel.WARNING:
            self._warning.append(result)
        else:
            self._error.append(result)

    def overall_status(self):
        if self._error:
            return seproxer_enums.ResultLevel.ERROR
        elif self._warning:
            return seproxer_enums.ResultLevel.WARNING
        return seproxer_enums.ResultLevel.OK

    @property
    def ok(self):
        return self._ok.copy()

    @property
    def warning(self):
        return self._warning.copy()

    @property
    def error(self):
        return self._error.copy()


class PageValidator(metaclass=abc.ABCMeta):
    """
    Interface for defining a page validator class which is used to validate
    the result of a loaded page.
    """
    @classmethod
    def class_name(cls):
        return cls.__name__

    def name(self):
        return self.class_name()

    @abc.abstractmethod
    def extend_results(self, driver: selenium.webdriver.remote.webdriver,
                       results: PageValidatorResults):
        """
        Performs the validation method and returns a Result object of the validation result.
        """


# This type allows any subclasses of PageValidator to work
PageValidatorType = t.TypeVar("PageValidatorType", bound=PageValidator)


class ConsoleErrorValidator(PageValidator):
    """
    This class ensures that there are no console errors present in the page.
    """
    ERROR_MESSAGE = "Errors in the console were present"
    WARNING_MESSAGE = "Warnings and/or network errors in the console were present"
    INFO_MESSAGE = "Info messages in the console were present"

    def __init__(self, check_js_injected_console: bool=False) -> None:
        self._check_js_injected_console = check_js_injected_console

    def _get_as_result(self, data: t.List[str], result_level: seproxer_enums.ResultLevel) -> Result:
        if result_level is seproxer_enums.ResultLevel.ERROR:
            msg = ConsoleErrorValidator.ERROR_MESSAGE
        elif result_level is seproxer_enums.ResultLevel.WARNING:
            msg = ConsoleErrorValidator.WARNING_MESSAGE
        else:
            msg = ConsoleErrorValidator.INFO_MESSAGE

        return Result(
            name=self.name(),
            status=result_level,
            message=msg,
            data=data,
        )

    @staticmethod
    def _get_result_from_driver_log(driver: selenium.webdriver.remote.webdriver
                                    ) -> t.Tuple[set, set, set]:
        warnings = set()
        errors = set()
        info = set()

        for log in driver.get_log("browser"):
            log_level = log.get("level")
            # An error occurred! Typically this will be introduced from the following:
            # 1) Stack trace
            # 2) console.error
            # 3) Network error (404, etc)
            if log_level == "SEVERE":
                # We don't want to indicate network errors as an Error because some network errors
                # will be a 404 which we will set as warnings
                if log.get("source") == "network":
                    warnings.add(log.get("message"))
                else:
                    errors.add(log.get("message"))
            elif log_level == "WARNING":
                warnings.add(log.get("message"))
            elif log_level in ("INFO", "DEBUG"):
                info.add(log.get("message"))

        return info, warnings, errors

    @staticmethod
    def _get_result_from_injected_js(driver: selenium.webdriver.remote.webdriver
                                     ) -> t.Tuple[set, set, set]:
        # TODO: put the container variable name in a static location
        log_container = driver.execute_script("return window.__seproxer_logs;")
        if not log_container:
            logger.warning("Unable to extract __seproxer_logs from js console")
            log_container = {}

        errors = set(log_container.get("error", []))
        warnings = set(log_container.get("warning", []))
        info = set(log_container.get("info", []))

        return info, warnings, errors

    def extend_results(self, driver: selenium.webdriver.remote.webdriver,
                       results: PageValidatorResults):
        # TODO: The following is ugly, could be significantly improved, it'll do for now
        if self._check_js_injected_console:
            info, warnings, errors = self._get_result_from_injected_js(driver)
        else:
            info, warnings, errors = self._get_result_from_driver_log(driver)

        if info:
            results.append(self._get_as_result(list(info), seproxer_enums.ResultLevel.OK))
        if warnings:
            results.append(self._get_as_result(list(warnings), seproxer_enums.ResultLevel.WARNING))
        if errors:
            results.append(self._get_as_result(list(errors), seproxer_enums.ResultLevel.ERROR))
