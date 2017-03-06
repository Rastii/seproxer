Seproxer
^^^^^^^^

This project provides developers and quality assurance engineers to ensure that a web
application does not break for end users before deploying to production.  This is not meant
to replace unit tests, instead, it is meant to be ran on top of unit tests to attempt to
catch errors that may have been missed.

Currently, this checks for javascript breaking on a page by retrieving console log messages
from iterating through a set of URLs provided.  If any error is observed, it is logged
to a results JSON file and a mitmproxy dump of the requests / responses are stored.  This dump
allows the developers to replay the exact server responses that caused the initial error.


Example
=======

Testing all of our endpoints using custom headers for authentication:

.. code-block:: bash

    $ seproxer --set-headers ":~q ~d test.mydomain.com:Cookie:SESSION=abcDEF123" \
               --strip-headers ":~d test.mydomain.com:Cookie \
               endpoints.txt

In this example, seproxer will iterate through all URLs that are stored in ``endpoints.txt``
and inject ``SESSION=abcDEF123`` cookie into ALL requests that match the ``test.mydomain.com``
domain.  The mitmproxy dump that are stored will strip any headers that match ``Cookie``
due to the ``--strip-headers`` option.  Any errors that are be found will be recorded
in the ``results.json`` and will look like the following:

.. code-block:: json

  {
    "errors": [
      {
        "data": [
          "test.mydomain.com/test 12:8 \"This is an error!\"",
          "test.mydomain.com/test 16:10 Uncaught TypeError: Cannot set property 'bar' of undefined"
        ],
        "message": "Errors in the console were present",
        "type": "ConsoleErrorValidator"
      }
    ],
    "known_states": {
      "angularloadedstate": true
    },
    "status": "ERROR",
    "successes": [],
    "time": "2017-03-05 19:43:55",
    "url": "test.mydomain.com/test",
    "uuid": "964b02c5-3356-46de-8621-bf57f47a6e71",
    "warnings": [
      {
        "data": [
          "test.mydomain.com/test 11:8 \"This is an warning!\"",
          "test.mydomain.com/favicon.ico - Failed to load resource: the server responded with a status of 404 (NOT FOUND)"
        ],
        "message": "Warnings and/or network errors in the console were present",
        "type": "ConsoleErrorValidator"
      }
    ]
  }

The respective mitmproxy dump can be found in the ``flows`` directory with the uuid as the
filename: ``964b02c5-3356-46de-8621-bf57f47a6e71.flow``.

Dependencies
============

Mitmproxy
---------
This project uses `mitmproxy <https://mitmproxy.org/>`_, please install any dependencies
for mitmproxy located `here <http://docs.mitmproxy.org/en/stable/install.html>`_.

Chrome WebDriver
----------------
To test with chrome, the chrome webdriver must be installed.
More information about installing the chrome webdriver can be located
`here <https://sites.google.com/a/chromium.org/chromedriver/downloads>`_.

PhantomJS WebDriver
-------------------
To test headless with PhantomJS, please download and install PhantomJS
`here <http://phantomjs.org/download.html>`_.

Firefox WebDriver
-----------------
To test with firefox (note, only firefox version >= 52 is supported)
please use the geckodriver found
`here <https://github.com/mozilla/geckodriver/releases>`_.


Installation
============

To install seproxer from github, please use the following commands:

.. code-block:: bash

    git clone https://github.com/rastii/seproxer.git
    cd seproxer
    python setup.py build
    sudo python setup.py install

After following the commands, seproxer should be available via ``seproxer``.


TODO
====
* More docs
* IE + Windows support
* Detecting all major JS frameworks
* Tests
