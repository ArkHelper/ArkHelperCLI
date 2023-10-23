import logging
from os import times
from Libs.skland_auto_sign_runner import run_auto_sign
from Libs.maa_runner import run_all_tasks
from Libs.utils import get_cur_time_f

import time
import var

interval = 55


async def start_scheduler():
    var.global_config["plan"] = sorted(
        var.global_config["plan"], key=lambda x: x["time"])

    next_task: dict = {}
    next_time: int = 0

    def get_next():
        nonlocal next_task
        nonlocal next_time

        cur = get_cur_time_f()
        next_task = next((item for item in var.global_config["plan"] if item.get(
            'time', 0) > cur), var.global_config["plan"][0])
        next_time = next_task["time"]

        logging.debug(f"scheduler task updated to {next_task}")

    logging.info(f"scheduler started, interval {interval} seconds")
    get_next()

    while (True):
        cur = get_cur_time_f()
        if (cur == next_time):
            _task = next_task["task"]

            logging.info(
                f"cur time is {cur} and task time is {next_time}. scheduler task {_task} is starting")

            if "skland" in _task:
                run_auto_sign()
            if "maa" in _task:
                await run_all_tasks()

            get_next()
        else:
            logging.debug(
                f"cur time is {cur} and task time is {next_time}. scheduler task {next_task} is waiting")

        time.sleep(interval)
