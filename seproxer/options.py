import typing as t
import enum
import os

from seproxer import seproxer_enums


class OptionError(Exception):
    """
    Generic option error for this module
    """


class FileConfigError(OptionError):
    """
    Error with file configuration
    """


class Defaults(enum.Enum):
    WEBDRIVER_TYPE = seproxer_enums.SeleniumBrowserTypes.PHANTOM_JS

    PROXY_PORT = 5050

    RESULTS_DIRECTORY = "results"
    RESULTS_FILE_NAME = "results.json"
    RESULTS_FILE_LEVEL = seproxer_enums.ResultLevel.WARNING

    FLOW_STORAGE_LEVEL = seproxer_enums.ResultLevel.WARNING

    ANGULAR_TIMEOUT = 20

    # The following class methods is to make mypy happy!

    @classmethod
    def driver_type(cls) -> seproxer_enums.SeleniumBrowserTypes:
        return cls.WEBDRIVER_TYPE.value

    @classmethod
    def results_file_level(cls) -> seproxer_enums.ResultLevel:
        return cls.RESULTS_FILE_LEVEL.value

    @classmethod
    def flow_level(cls) -> seproxer_enums.ResultLevel:
        return cls.FLOW_STORAGE_LEVEL.value


class Options:
    def __init__(
            self,
            selenium_webdriver_type: seproxer_enums.SeleniumBrowserTypes=Defaults.driver_type(),
            selenium_webdriver_path: t.Optional[str]=None,
            mitmproxy_port: int=Defaults.PROXY_PORT.value,
            ignore_certificates: bool=False,
            # Flow storing
            flow_storage_level: t.Optional[seproxer_enums.ResultLevel]=Defaults.flow_level(),
            # Log handling options
            file_results_level: t.Optional[seproxer_enums.ResultLevel]=(
                Defaults.results_file_level()
            ),
            results_directory: str=Defaults.RESULTS_DIRECTORY.value,
            file_results_file_name: str=Defaults.RESULTS_FILE_NAME.value,
            # Inject headers into arbitrary requests using mitmproxy
            set_headers: t.Optional[t.Sequence[t.Tuple[str, str, str]]]=None,
            # Strip headers when storing results
            strip_headers: t.Optional[t.Sequence[t.Tuple[str, str]]]=None,
            check_angular_state: int=True,
            angular_state_timeout: int=Defaults.ANGULAR_TIMEOUT.value,
            console_error_detection: int=True,
            ) -> None:

        self.selenium_webdriver_type = selenium_webdriver_type
        self.selenium_webdriver_path = selenium_webdriver_path

        self.mitmproxy_port = mitmproxy_port
        self.ignore_certificates = ignore_certificates

        self.results_directory = results_directory

        self.flow_storage_level = flow_storage_level

        self.file_results_level = file_results_level
        self.file_results_file_name = file_results_file_name

        self.set_headers = set_headers or []
        self.strip_headers = strip_headers or []

        # State loaders
        self.check_angular_app = check_angular_state
        self.angular_state_timeout = angular_state_timeout

        # Validators
        self.console_error_detection = console_error_detection

        # Ensure that our results file name directory is setup properly
        self.setup_file_results_dir()

    def setup_file_results_dir(self):
        results_directory_path = os.path.expanduser(self.results_directory)
        os.makedirs("{}/flows".format(results_directory_path), exist_ok=True)

        results_file_path = "{}/{}".format(results_directory_path, self.file_results_file_name)
        if os.path.exists(results_file_path) and not os.path.isfile(results_file_path):
            raise FileConfigError(
                "Results file '{}' exists but it not a valid file".format(results_file_path))
