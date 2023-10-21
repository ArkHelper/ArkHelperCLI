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

from Libs.MAA.asst.asst import Asst
from Libs.maa_asst_instance_runner import run_and_init_asst_inst
from Libs.skland_auto_sign_runner import run_auto_sign
from Libs.utils import read_config_and_validate, get_logging_handlers, kill_processes_by_name



var.cli_env = pathlib.Path(__file__, "../")
var.asst_res_lib_env = var.cli_env / "RuntimeComponents" / "MAA"
var.lock = {
    'list': threading.Lock(),
    'asst': threading.Lock()
}

logging.basicConfig(level=logging.DEBUG,
                    # filename=str(current_path / "Log" / "log.log"),
                    # encoding="utf-8",
                    handlers=get_logging_handlers(),
                    format="%(asctime)s[%(levelname)s] %(message)s")


async def main():
    var.global_config = read_config_and_validate("global")
    var.personal_configs = read_config_and_validate("personal")

    logging.info(f"started up at {var.cli_env}")
    logging.info(f"with global config {var.global_config}")
    logging.info(f"with personal config {var.personal_configs}")

    # load_res()
    # run_auto_sign(current_path)

    async_enabled = False

    if False:
        async_task_ls = []
        for dev in var.global_config.get("devices"):
            task = asyncio.to_thread(
                run_and_init_asst_inst, dev, global_config, personal_config, lock)
            async_task_ls.append(task)

        await asyncio.gather(*async_task_ls)
    else:
        for dev in var.global_config.get("devices"):
            run_and_init_asst_inst(dev)

    #kill_processes_by_name("MuMuVMMHeadless.exe")

    logging.info(f"everything completed. exit")


if __name__ == "__main__":
    asyncio.run(main())
