from seproxer.selenium_extensions.states import base

from selenium.webdriver.remote import webdriver


class AngularLoadedState(base.LoadedStateHandler):
    """
    This loaded state checks to see if Angular is part of the application and if so,
    checks to make sure angular
    """
    def is_state_supported(self, driver: webdriver):
        """
        We simply need to know if angular is available
        """
        return driver.execute_script("return (window.angular !== undefined)")

    def check(self, driver: webdriver):
        return driver.execute_script(
            "return (window.angular !== undefined) && "
            "(angular.element(document).injector() !== undefined) && "
            "(angular.element(document).injector().get('$http').pendingRequests.length === 0)"
        )
