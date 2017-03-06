import typing as t

import seproxer.options
from seproxer import seproxer_enums

from seproxer.selenium_extensions import validators


class PageValidatorManager:
    def __init__(self,
                 initial_validators: t.Optional[t.List[validators.PageValidatorType]]=None) -> None:

        if initial_validators is None:
            initial_validators = []

        self._validators = {v.name(): v for v in initial_validators}

    def add_validator(self, validator: validators.PageValidatorType):
        self._validators[validator.name()] = validator

    def get_validator(self, validator_name: str):
        return self._validators.get(validator_name)

    def validate(self, driver) -> validators.PageValidatorResults:
        # TODO: implement this via async coroutines
        results = validators.PageValidatorResults()
        for validator in self._validators.values():
            validator.extend_results(driver, results)

        return results

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "PageValidatorManager":
        managed_validators = []
        if options.console_error_detection:
            validator = validators.ConsoleErrorValidator(
                check_js_injected_console=(
                    options.selenium_webdriver_type is seproxer_enums.SeleniumBrowserTypes.FIREFOX
                )
            )
            managed_validators.append(validator)

        return PageValidatorManager(managed_validators)
