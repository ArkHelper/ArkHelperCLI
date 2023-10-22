import json
from math import fabs
import pathlib
import time
import sys
import os
import logging
import asyncio
import threading

import var

from Libs.maa_runner import run_all_tasks
from Libs.skland_auto_sign_runner import run_auto_sign
from Libs.utils import read_config_and_validate, get_logging_handlers


var.cli_env = pathlib.Path(__file__, "../")
var.asst_res_lib_env = var.cli_env / "RuntimeComponents" / "MAA"
var.lock = {'list': threading.Lock(), 'asst': threading.Lock()}
var.global_config = read_config_and_validate("global")
var.personal_configs = read_config_and_validate("personal")


logging.basicConfig(level=logging.DEBUG,
                    # filename=str(current_path / "Log" / "log.log"),
                    # encoding="utf-8",
                    handlers=get_logging_handlers(),
                    format="%(asctime)s[%(levelname)s] %(message)s")


async def main():
    logging.info(f"started up at {var.cli_env}")
    logging.info(f"with global config {var.global_config}")
    logging.info(f"with personal config {var.personal_configs}")

    # load_res()
    await run_all_tasks()
    # run_auto_sign(current_path)

    logging.info(f"everything completed. exit")


if __name__ == "__main__":
    asyncio.run(main())
