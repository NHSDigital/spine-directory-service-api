"""
When you're running pytest this module will log into 'pytest' logs.

You can control pytests logging options as described here, so we don't
need to re-invent the wheel.

https://docs.pytest.org/en/7.1.x/how-to/logging.html
"""
import typing
import logging
import inspect
import functools
import uuid
import json
import os
from datetime import datetime

logging.METHOD = 5
logging.addLevelName(logging.METHOD, "METHOD")
logging.Logger.method = lambda inst, msg, *args, **kwargs: inst.log(
    logging.METHOD, msg, *args, **kwargs
)
logging.LoggerAdapter.method = lambda inst, msg, *args, **kwargs: inst.log(
    logging.METHOD, msg, *args, **kwargs
)
logging.method = lambda msg, *args, **kwargs: logging.log(
    logging.METHOD, msg, *args, **kwargs
)

# Use this elswhere
log = logging.getLogger(__name__)


def log_method(f):
    """
    Logs a functions entry and exit.
    Includes args, kwargs, return values, and exceptions.
    Tags each entry/exit pair with a uuid4 for correlation.

    It puts it at a SUPER-LOW logging level (5).
    """

    def pre_log(f, *args, **kwargs):
        log_line = {
            "timestamp": datetime.utcnow().isoformat(),
            "function_name": f.__name__,
            "id": str(uuid.uuid4()),  # use this to match function entry/exit
            "type": "generator" if inspect.isgeneratorfunction(f) else "function",
            "location": "entry",
            "args": list(args),
            "kwargs": dict(**kwargs),
        }
        log.method(log_line)
        return log_line

    def log_and_reraise(log_line, e):
        log_line["exception"] = str(e)
        log.method(log_line)
        raise e

    def post_log(log_line, **extra):
        log_line["location"] = "exit"
        log_line["timestamp"] = datetime.utcnow().isoformat()
        log_line.update(extra)
        log.method(log_line)

    @functools.wraps(f)
    def log_generator(*args, **kwargs):
        log_line = pre_log(f, *args, **kwargs)
        try:
            yield from f(*args, **kwargs)
        except Exception as e:
            log_and_reraise(log_line, e)
        post_log(log_line)

    @functools.wraps(f)
    def log_function(*args, **kwargs):
        log_line = pre_log(f, *args, **kwargs)
        try:
            output = f(*args, **kwargs)
        except Exception as e:
            log_and_reraise(log_line, e)
        post_log(log_line, output=output)
        return output

    return log_generator if inspect.isgeneratorfunction(f) else log_function


def _jsonify(line):
    if isinstance(line, str):
        return line
    try:
        return json.dumps(line, default=str)
    except json.JSONDecodeError:
        return str(line)
