import signal
import functools
import logging
import sys

import seproxer.cmdline
import seproxer.main


logger = logging.getLogger(__name__)


def graceful_exit(seproxer_runner: seproxer.main.Seproxer, signum, frame):
    _ = frame  # NOQA
    logger.info("Caught signum: {}, shutting down".format(signum))
    seproxer_runner.done()


def main(args=None):
    # Get options
    parsed_args = seproxer.cmdline.get_parsed_args(args=args)
    options = seproxer.cmdline.get_seproxer_options(parsed_args)

    # Start runner
    seproxer_runner = seproxer.main.Seproxer.from_options(options)

    # Create a handler for SIGINT
    signal.signal(signal.SIGINT, functools.partial(graceful_exit, seproxer_runner))

    # Test our URLS
    try:
        seproxer_runner.test_urls(parsed_args.test_urls)
    except KeyboardInterrupt:
        sys.exit(1)
    finally:
        seproxer_runner.done()


if __name__ == "__main__":
    main()
