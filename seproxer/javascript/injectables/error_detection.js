/**
 * Self injecting script that adds an error event handler via window.onerror and
 * the hooks the console logging methods to store any console logging activity.
 */
(function($window) {
    if($window.__seproxer_logs !== undefined) {
        return;
    }
    $window.__seproxer_logs = {
        error: [],
        warning: [],
        info: []
    };

    $window.onerror = function(msg, url, lineNo, columnNo, error) {
        var message = [
            url,
            lineNo + ":" + columnNo,
            JSON.stringify(error) ? error : msg
        ].join(' - ');
        $window.__seproxer_logs.error.push(message);
    };

    Function.prototype.__seproxerMakeLog = function(container) {
        var self = this;
        return function() {
            var args = Array.prototype.slice.call(arguments).map(function(e) {
                // Leave them strings alone
                if((typeof e) === "string") {
                    return e;
                }
                return JSON.stringify(e);
            });
            container.push(args.join(" "));
            return self.apply(self, args);
        };
    };

    // We also want to log any console log messages!
    $window.console.log = $window.console.log.__seproxerMakeLog($window.__seproxer_logs.info);
    $window.console.info = $window.console.info.__seproxerMakeLog($window.__seproxer_logs.info);
    $window.console.warn = $window.console.warn.__seproxerMakeLog($window.__seproxer_logs.warning);
    $window.console.error = $window.console.error.__seproxerMakeLog($window.__seproxer_logs.error);

})(window);