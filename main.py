import json
import pathlib
import time
import sys
import os
import logging
import asyncio

from Libs.MAA.asst.asst import Asst
from Libs.maa_personal_scht_runner import add_personal_scht_tasks_to_inst
from Libs.maa_asst_instance_runner import run_and_init_asst_inst
from Libs.skland_auto_sign_runner import run_auto_sign
from Libs.maa_util import asst_callback
from Libs.maa_initer import init
from Libs.utils import read_config, get_logging_handlers,kill_processes_by_name

current_path = pathlib.Path(__file__, "../")


logging.basicConfig(level=logging.DEBUG,
                    # filename=str(current_path / 'Log' / 'log.log'),
                    # encoding='utf-8',
                    #handlers=get_logging_handlers(current_path), #TODO:logging有线程安全问题写入文件可能会导致致命错误找个时间替换掉
                    format='%(asctime)s[%(levelname)s] %(message)s')


async def main():
    global_config = read_config(current_path, 'global')
    personal_config = read_config(current_path, 'personal')

    logging.info(f"started up at {current_path}")
    logging.info(f"with global config {global_config}")
    logging.info(f"with personal config {personal_config}")

    init(current_path / 'RuntimeComponents' / 'MAA')

    # run_auto_sign(current_path)

    async_task_ls = []
    for dev in global_config.get("devices"):
        task = asyncio.to_thread(
            run_and_init_asst_inst, dev, global_config, personal_config)
        async_task_ls.append(task)

    await asyncio.gather(*async_task_ls)

    kill_processes_by_name("MuMuVMMHeadless.exe")

    logging.info(f"everything completed. exit")
    

if __name__ == "__main__":
    asyncio.run(main())
