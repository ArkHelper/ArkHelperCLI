import pathlib
import sys
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
var.verbose = "-v" in sys.argv or "--verbose" in sys.argv

logging.basicConfig(level=logging.DEBUG,
                    handlers=get_logging_handlers(logging.DEBUG,logging.DEBUG if var.verbose else logging.INFO),
                    format="%(asctime)s[%(levelname)s] %(message)s")


async def main():
    logging.info(f"started up at {var.cli_env}")
    logging.info(f"with global config {var.global_config}")
    logging.info(f"with personal config {var.personal_configs}")

    # load_res()
    await run_all_tasks()
    # run_auto_sign(current_path)

    logging.info(f"everything completed. exit")

asyncio.run(main())
