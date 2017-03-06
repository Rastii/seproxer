import typing as t
import os
import abc
import threading
import queue
import json
import uuid
import asyncio
import logging
import datetime

import seproxer.options
from seproxer import seproxer_enums


logger = logging.getLogger(__name__)


class Error(Exception):
    """
    Generic module level exception
    """


class ThreadStartedError(Error):
    """
    Exception occurs when an operation expects a thread to not be alive
    and the opposite is true.
    """


class ResultHandler(threading.Thread, metaclass=abc.ABCMeta):
    def __init__(self, results_queue: t.Optional[queue.Queue]=None) -> None:
        super().__init__(daemon=True)
        if not results_queue:
            results_queue = queue.Queue()
        self._results_queue = results_queue

    @classmethod
    def class_name(cls):
        return cls.__name__

    @property
    def handler_name(self) -> str:
        """
        The name of the handler, can be overwritten in inherited classes, defaults to
        the class name.
        """
        return self.class_name()

    def get_queue(self) -> queue.Queue:
        """
        Returns the results queue that was initialized with the thread object.
        """
        if self.is_alive():
            raise ThreadStartedError("Cannot retrieve queue while thread is alive!")

        return self._results_queue

    @abc.abstractmethod
    def supported_handle_types(self) -> tuple:
        """
        Returns what types are supported for this handler

        For example, if a handler handles WARNING and ERROR, this class method should
        return: (cls.TYPE_WARNING, cls.TYPE_ERROR)
        """

    @abc.abstractmethod
    def process_result(self, result):
        """
        Implement this method for processing!
        """

    def run(self):
        # Run continuously until we retrieve a result from the queue and then process it
        while True:
            result_to_process = self._results_queue.get()
            try:
                self.process_result(result_to_process)
            except Exception:
                logger.exception("Error processing handler '{}'".format(self.handler_name))
            finally:
                self._results_queue.task_done()


async def await_for_queues(queues):
    loop = asyncio.get_event_loop()
    blocking_queue_joins = [loop.run_in_executor(None, q.join) for q in queues]
    await asyncio.wait(blocking_queue_joins)


class ResultHandlerManager:
    def __init__(self, initial_handlers: t.Optional[t.Iterable[ResultHandler]]=None) -> None:
        self._handlers = []  # type: t.List[ResultHandler]

        if not initial_handlers:
            initial_handlers = []

        for handler in initial_handlers:
            self.add_handler(handler)

    def add_handler(self, handler):
        self._handlers.append((handler, handler.get_queue()))
        # Start the handler
        handler.start()

    def handle(self, result):
        for handler, handler_queue in self._handlers:
            if result.status_code in handler.supported_handle_types():
                handler_queue.put(result)

    def done(self):
        # All we need to do is simply wait for all of our queues to be empty
        loop = asyncio.get_event_loop()
        queues = (h[1] for h in self._handlers)
        try:
            loop.run_until_complete(await_for_queues(queues))
        finally:
            loop.close()

    @staticmethod
    def from_options(options: seproxer.options.Options) -> "ResultHandlerManager":
        initial_handlers = []  # type: t.List[ResultHandler]
        if options.file_results_level is not None:
            initial_handlers.append(
                FileLogHandler(
                    results_directory=options.results_directory,
                    results_file_name=options.file_results_file_name,
                    file_level=options.file_results_level,
                )
            )
        if options.flow_storage_level is not None:
            initial_handlers.append(
                FlowFileHandler(
                    results_directory=options.results_directory,
                    store_flow_level=options.flow_storage_level,
                )
            )

        return ResultHandlerManager(initial_handlers=initial_handlers)


class FlowFileHandler(ResultHandler):
    def __init__(self,
                 results_directory: str,
                 store_flow_level: seproxer_enums.ResultLevel=seproxer_enums.ResultLevel.ERROR
                 ) -> None:
        super().__init__()

        self._results_flow_directory = "{}/flows".format(results_directory)
        self._supported_handle_types = store_flow_level.cascaded()

        self._flow_file_format = self._results_flow_directory + "/{}.flow"

    def supported_handle_types(self):
        return self._supported_handle_types

    def process_result(self, result):
        flow_file = self._flow_file_format.format(result.uuid)
        with open(flow_file, "wb") as fp:
            fp.write(result.proxy_results)


class FileLogHandler(ResultHandler):
    def __init__(self, results_directory, results_file_name,
                 file_level: seproxer_enums.ResultLevel=seproxer_enums.ResultLevel.ERROR) -> None:
        super().__init__()

        self._results_directory = results_directory
        self._results_file_name = "results.json"
        self._results_file_path = "{}/{}".format(results_directory, results_file_name)

        self._supported_handle_types = file_level.cascaded()

    @staticmethod
    def _result_template(result):
        return {
            "url": result.url,
            "uuid": result.uuid,
            "time": str(datetime.datetime.now().replace(microsecond=0)),
            "known_states": {
                s.name: s.is_state_reached
                for s in result.state_results if s.is_supported
            },
            "status": result.status_code.name,
            "successes": [r.as_dict() for r in result.validator_results.ok],
            "errors": [r.as_dict() for r in result.validator_results.error],
            "warnings": [r.as_dict() for r in result.validator_results.warning],
        }

    def supported_handle_types(self):
        return self._supported_handle_types

    def _load_stored_result_from_file(self, default=None):
        # First, let's attempt to load the existing results json file
        try:
            with open(self._results_file_path) as fp:
                file_data = fp.read()
        except IOError:
            return default

        # Now attempt to deserialize the file... if that fails, save a backup of the file
        try:
            return json.loads(file_data)
        except json.JSONDecodeError as e:
            backup_file_name = "corrupted.{}.{}".format(
                str(uuid.uuid4())[:8],
                self._results_file_name,
            )
            logger.error(
                "Unable to parse file {}: {}, renaming to {} and creating new file".format(
                    self._results_file_path, e, backup_file_name,
                )
            )
            dst = "{}/{}".format(self._results_directory, backup_file_name)
            os.rename(self._results_file_path, dst)

        return default

    def process_result(self, result):
        # First, attempt to load a stored result from
        saved_data = self._load_stored_result_from_file(default=[])

        # Create our data to save
        result_data = self._result_template(result)
        saved_data.append(result_data)

        # Finally, write the saved data
        with open(self._results_file_path, "w") as fp:
            fp.write(json.dumps(saved_data, indent=2, sort_keys=True))
