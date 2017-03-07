import functools

import seproxer.seproxer_enums
from seproxer import options

import selenium.webdriver
from selenium.webdriver.common import desired_capabilities
from selenium.webdriver.remote import webdriver as remote_webdriver


FACTORY_DISPATCHER = {}


class Error(Exception):
    """
    Generic module level error
    """


class InvalidBrowserType(Error):
    """
    Specified browser type is not valid and/or a factory method for it
    has not been implemented.
    """


class SeleniumDriverError(Error):
    """
    Error instantiating selenium_extensions driver from specified settings
    """


def register_factory(browser_type: seproxer.seproxer_enums.SeleniumBrowserTypes):
    def decorator(func):
        FACTORY_DISPATCHER[browser_type] = func

        @functools.wraps
        def factory_function(*args, **kwargs):
            return func(*args, **kwargs)
        return factory_function
    return decorator


@register_factory(seproxer.seproxer_enums.SeleniumBrowserTypes.CHROME)
def chrome_webdriver(opts: options.Options) -> selenium.webdriver.Chrome:
    chrome_options = selenium.webdriver.ChromeOptions()
    chrome_options.add_argument("--proxy-server=127.0.0.1:{}".format(opts.mitmproxy_port))
    # We will always ignore certificates going to the proxy!
    chrome_options.add_argument("--ignore-certificate-errors")

    args = {
        "chrome_options": chrome_options,
    }
    if opts.selenium_webdriver_path:
        args["executable_path"] = opts.selenium_webdriver_path

    return selenium.webdriver.Chrome(**args)


@register_factory(seproxer.seproxer_enums.SeleniumBrowserTypes.PHANTOM_JS)
def phantom_js_webdriver(opts: options.Options) -> selenium.webdriver.PhantomJS:
    service_args = [
        "--proxy=127.0.0.1:{}".format(opts.mitmproxy_port),
        "--proxy-type=http",
        "--ignore-ssl-errors=true",
    ]

    args = {
        "service_args": service_args,
    }
    if opts.selenium_webdriver_path:
        args["executable_path"] = [opts.selenium_webdriver_path]

    driver = selenium.webdriver.PhantomJS(**args)
    driver.set_window_size(1920, 1080)
    return driver


@register_factory(seproxer.seproxer_enums.SeleniumBrowserTypes.FIREFOX)
def firefox_webdriver(opts: options.Options) -> selenium.webdriver.Firefox:
    firefox_profile = selenium.webdriver.FirefoxProfile()
    firefox_profile.set_preference("network.proxy.no_proxies_on", "")
    firefox_profile.set_preference("network.proxy.http", "127.0.0.1")
    firefox_profile.set_preference("network.proxy.http_port", opts.mitmproxy_port)
    firefox_profile.set_preference("network.proxy.ssl", "127.0.0.1")
    firefox_profile.set_preference("network.proxy.ssl_port", opts.mitmproxy_port)
    firefox_profile.set_preference("network.proxy.type", 1)
    firefox_profile.update_preferences()

    capabilities = desired_capabilities.DesiredCapabilities.FIREFOX.copy()
    capabilities["acceptInsecureCerts"] = True

    args = {
        "capabilities": capabilities,
        "firefox_profile": firefox_profile,
    }
    if opts.selenium_webdriver_path:
        args["executable_path"] = opts.selenium_webdriver_path

    return selenium.webdriver.Firefox(**args)


def get_webdriver(options: seproxer.options.Options) -> remote_webdriver.WebDriver:
    browser_type = options.selenium_webdriver_type

    factory_function = FACTORY_DISPATCHER.get(options.selenium_webdriver_type)
    if not factory_function:
        raise InvalidBrowserType("Specified browser type: {} is not supported".format(browser_type))

    return factory_function(options)
