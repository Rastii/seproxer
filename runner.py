import seproxer.cmdline
import seproxer.main


def main(args=None):
    parsed_args = seproxer.cmdline.get_parsed_args(args=args)
    options = seproxer.cmdline.get_seproxer_options(parsed_args)

    seproxer_runner = seproxer.main.Seproxer.from_options(options)
    seproxer_runner.test_urls(parsed_args.test_urls)
    seproxer_runner.done()


if __name__ == "__main__":
    main()
