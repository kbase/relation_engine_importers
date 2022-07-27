import functools
import inspect
import json
import numpy as np
import os
import subprocess
import sys
import time as time

DEBUG = os.environ.get("DEBUG", 1)


run_bash = functools.partial(
    subprocess.run,
    stdout=sys.stdout,
    stderr=sys.stderr,
    shell=True,
    executable="/bin/bash",
)

print = functools.partial(__builtins__["print"], file=sys.stderr)

TAG_WIDTH = 120
TAG_BEGIN = TAG_WIDTH * "#"
TAG_END = TAG_WIDTH * "-"
MAX_LINES = 15


def jprint(o, dry_run=False):
    s = json.dumps(o, indent=4, default=str)
    if not dry_run:
        print(s)
    return s


def dprint(
    *args,
    run: str = "py",
    format_json: bool = True,
    where: bool = False,
    time_it: bool = False,
    max_lines: int = MAX_LINES,
    exit: bool = False,
    subproc_kw: dict = None,
    print_kw: dict = None,
    tb: int = 0,
):
    """Debug print, with the option of executing the args in python or bash

    :param run:         Whether to execute var args in python or bash,
                        Defaults to "py"
    :param format_json: Whether to format JSON,
                        Defaults to True
    :param where:       Whether to output information about the file/func/lineno,
                        Defaults to False
    :param time_it:     Whether to output timing information,
                        Defaults to False
    :param max_lines:   Max lines to pring per var arg,
                        Defaults to MAX_LINES
    :param exit:        Whether to exit at the end,
                        Defaults to False
    :param subproc_kw:  subprocess.run kwargs,
                        Defaults to {}
    :param print_kw:    print kwargs,
                        Defaults to {}
    :param tb:          Lines of traceback to print
    :return:            For bash runs, the retcode
    """

    if not DEBUG:
        return

    if subproc_kw is None:
        subproc_kw = {}
    if print_kw is None:
        print_kw = {}

    if print_kw:
        global print
        print = functools.partial(print, **print_kw)

    def print_format(arg):
        if format_json and isinstance(arg, (dict, list)):
            arg_json = jprint(arg, dry_run=True)
            if max_lines is not None and arg_json.count("\n") > max_lines:
                arg_json = "\n".join(arg_json.split("\n")[0: max_lines] + ["..."])
            print(arg_json)
        else:
            print(arg)

    print(TAG_BEGIN)

    if where:
        stack = inspect.stack()
        print(
            "[[File: %s, Function: %s, Line: %d]]"
            % (stack[1][1], stack[1][3], stack[1][2])
        )

    if tb:
        args.insert(0, f"import tb; tb.print_traceback(limit={tb}")

    for arg in args:
        if time_it:
            t0 = time.time()
        if run:
            print(">> " + arg)
            if run in ["cli", "shell", "bash", "proc"]:
                completed_proc = run_bash(arg, **subproc_kw)
                retcode = completed_proc.returncode
            elif run in ["py", "python"]:
                frame = inspect.stack()[1].frame
                env = {**frame.f_globals, **frame.f_locals}
                print_format(eval(arg, env))
            # Backwards compatibility when the python namespace
            # used to be passed in manually like
            # `dprint(..., run={**globals(), **locals()})`
            elif isinstance(run, dict):
                print_format(eval(arg, run))
            else:
                raise ValueError(f"Unknown arg run={run}")
        else:
            print_format(arg)
        if time_it:
            t = time.time() - t0
            print("[[Completed in %.2fs]]" % t)

    print(TAG_END)

    if exit:
        sys.exit(0)

    # return last retcode
    if run in ["cli", "shell"]:
        return retcode


def where_am_i(f):
    """Function decorator printing module/function names

    :param f: Function to be decorated
    """

    def f_new(*a, **kw):
        dprint(
            "[[Where am I? In module: %s, function: %s]]" % (globals()["__name__"], f.__qualname__),
            run=None
        )
        f(*a, **kw)

    return f_new


class ProgressKeeper:
    def __init__(self, update_epoch, total):
        """Print progress statistics

        :param update_epoch:    Print progress statistics every this number of iterations
        :param total:           Total number of iterations
        """
        self.update_epoch = update_epoch
        self.total = total

        self.times = []

    def __enter__(self):
        print("\n\n")
        print(TAG_BEGIN)
        self.t0 = time.time()

    def __exit__(self):
        del self.times
        print(TAG_END)
        print("\n\n")

    def keep_progress(self, i):
        if not i % self.update_epoch:
            if i != 0:
                t = time.time() - self.t0
                self.times.append(t)
                print("%.2fs/iter ..." % (np.mean(self.times) / self.update_epoch), end=" ")
            print("%d/%d iters, " % (i, self.total), end=" ")
            self.t0 = time.time()
