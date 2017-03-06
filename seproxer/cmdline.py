import argparse

import seproxer.seproxer_enums
from seproxer import options

import mitmproxy.tools.cmdline


class CmdlineError(Exception):
    """
    Generic exception for the cmdline module
    """


class InvalidOptionValue(CmdlineError):
    """
    Exception when the specified option value could not be valided
    """


class InvalidEnumActionType(CmdlineError):
    """
    Raised when an invalid enum type is specified -- programmer error
    """


class EnumAction(argparse.Action):
    def __init__(self, option_strings, enum_type=None, dest=None, choices=None, **kwargs):
        if not enum_type:
            raise InvalidEnumActionType("No enum type specified!")

        self._enum_type = enum_type
        # Override the choices to use this enum_type as well
        if not choices:
            choices = [e.name for e in enum_type]

        super().__init__(option_strings, dest, choices=choices, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        _ = parser, option_string  # NOQA

        try:
            result = self._enum_type[values]
        except KeyError:
            raise argparse.ArgumentError(
                self, "{} not a valid choice of {}".format(values, self.choices))

        setattr(namespace, self.dest, result)


class UrlFile(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        try:
            with open(values) as fp:
                urls = [url.strip() for url in fp.readlines() if url]
        except IOError as e:
            raise argparse.ArgumentError(self, "Unable to read URL file: {}".format(e))

        setattr(namespace, self.dest, urls)


def add_selenium_options(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("Selenium arguments")

    group.add_argument(  # type: ignore
        "--browser-type",
        type=str,
        help="Specify the browser type to use for selenium_extensions",
        default=options.Defaults.WEBDRIVER_TYPE.value,
        action=EnumAction,
        enum_type=seproxer.seproxer_enums.SeleniumBrowserTypes,
    )
    group.add_argument(
        "--driver-path",
        type=str,
        default=None,
        help="The path to the selenium_extensions browser driver",
    )


def _set_headers_type(header):
    try:
        return mitmproxy.tools.cmdline.parse_setheader(header)
    except mitmproxy.tools.cmdline.ParseException as e:
        raise InvalidOptionValue("The specified set_headers value is incorrect: {}".format(e))


def _strip_headers_type(header):
    """
    Same as the set_headers type, except we exclude the value
    """
    patt, a, _ = _set_headers_type(header)
    return patt, a


def add_proxy_options(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("Proxy arguments")
    group.add_argument(
        "--proxy-port",
        type=int,
        default=options.Defaults.PROXY_PORT.value,
        help="Specify the port that mitmproxy will use.  The Selenium browser will "
             "also be configured to use this port.",
    )
    group.add_argument(
        "--set-headers",
        action="append",
        type=_set_headers_type,
        metavar="PATTERN",
        help="Set the headers that will be injected into the requests.  This can be useful when "
             "adding cookies bypassing login routines.",
    )
    group.add_argument(
        "--strip-headers",
        action="append",
        type=_strip_headers_type,
        metavar="PATTERN",
        help="Define a pattern to strip headers from the stored flows.  This is like the "
             "set-header parameter; however, no value is required",
    )
    group.add_argument(
        "--ignore-certificates",
        action="store_true",
        default=False,
        help="Ignore SSL/TLS certificates of the servers that the proxy sends requests to",
    )


def add_state_options(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("State arguments")
    group.add_argument(
        "--disable-state-angular",
        action="store_true",
        default=False,
        help="Disable checking for the presence of an angular application",
    )
    group.add_argument(
        "--angular-state-timeout",
        type=str,
        default=options.Defaults.ANGULAR_TIMEOUT.value,
        help="The length of time to wait for an angular application before timing out",
    )


def add_validator_options(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("Validator arguments")
    group.add_argument(
        "--ignore-console",
        action="store_true",
        default=False,
        help="Set this value to ignore console messages",
    )


def add_storage_options(parser: argparse.ArgumentParser):
    group = parser.add_argument_group("Storage arguments")
    group.add_argument(
        "--results-directory",
        type=str,
        default=options.Defaults.RESULTS_DIRECTORY.value,
        help="The results will be stored in the specified directory",
    )
    group.add_argument(
        "--results-file-name",
        type=str,
        default=options.Defaults.RESULTS_FILE_NAME.value,
        help="The file name, in the results directory, that will be used to store "
             "the JSON results",
    )
    group.add_argument(  # type: ignore
        "--results-file-level",
        default=seproxer.seproxer_enums.ResultLevel.WARNING,
        help="The minimum level in which results will be stored",
        action=EnumAction,
        enum_type=seproxer.seproxer_enums.ResultLevel,
    )
    group.add_argument(
        "--disable-file-results",
        action="store_true",
        default=False,
        help="Setting this option will not save results to a file",
    )
    group.add_argument(
        "--disable-flow-storage",
        action="store_true",
        default=False,
        help="Setting this option will not save any mitmproxy flows",
    )


def get_parsed_args(args=None):
    parser = argparse.ArgumentParser(
        usage="""
        %(prog)s [options] URL_FILE

        Example with cookie injection
        -----------------------------
        %(prog)s --set-headers ":~q ~d example.com:Cookie:Nomz" \\
                  --strip-headers ":~d example.com:Cookie" \\
                  test_urls.txt

            Injects the Cookie=Nomz HEADER into all example.com DOMAIN REQUESTS
            (note that ~q matches requests that don't have a response yet and ~d matches domain)
            Please refer to the mitmproxy docs for filter expressions:
            http://docs.mitmproxy.org/en/stable/features/filters.html

            Additionally, this example will strip the Cookie header in the saved flows.
        """.strip()
    )
    parser.add_argument(
        "test_urls",
        metavar="URL_FILE",
        type=str,
        action=UrlFile,
        help="Specify a file that contains URLs separated by newlines"
    )

    add_selenium_options(parser)
    add_proxy_options(parser)
    add_state_options(parser)
    add_validator_options(parser)
    add_storage_options(parser)

    try:
        return parser.parse_args(args=args)
    except argparse.ArgumentError as e:
        raise CmdlineError(e)


def get_seproxer_options(parsed_args) -> seproxer.options.Options:
    if parsed_args.disable_flow_storage:
        flow_storage_level = None
    else:
        flow_storage_level = parsed_args.results_file_level

    if parsed_args.disable_flow_storage:
        file_storage_level = None
    else:
        file_storage_level = parsed_args.results_file_level

    return seproxer.options.Options(
        selenium_webdriver_type=parsed_args.browser_type,
        selenium_webdriver_path=parsed_args.driver_path,
        mitmproxy_port=parsed_args.proxy_port,
        ignore_certificates=parsed_args.ignore_certificates,
        flow_storage_level=flow_storage_level,
        file_results_level=file_storage_level,
        results_directory=parsed_args.results_directory,
        file_results_file_name=parsed_args.results_file_name,
        set_headers=parsed_args.set_headers,
        strip_headers=parsed_args.strip_headers,
        check_angular_state=not parsed_args.disable_state_angular,
        angular_state_timeout=parsed_args.angular_state_timeout,
        console_error_detection=not parsed_args.ignore_console,
    )
