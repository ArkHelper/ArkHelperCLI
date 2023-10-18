import json
import pathlib
import time
import sys
import os
import logging

from Libs.maa_personal_scht_runner import run_personal_scht_tasks
from Libs.skland_auto_sign_runner import run_auto_sign
from Libs.maa_util import asst_callback
from Libs.maa_initer import init
from Libs.utils import read_config, get_logging_handlers

current_path = pathlib.Path(__file__, "../")


logging.basicConfig(level=logging.DEBUG,
                    # filename=str(current_path / 'Log' / 'log.log'),
                    # encoding='utf-8',
                    handlers=get_logging_handlers(current_path),
                    format='%(asctime)s [%(levelname)s] %(message)s')


if __name__ == "__main__":
    global_config = read_config(current_path, 'global')
    personal_config = read_config(current_path, 'personal')

    logging.info(f"started up at {current_path}")
    logging.info(f"with global config {global_config}")
    logging.info(f"with personal config {personal_config}")

    asst = init(current_path / 'RuntimeComponents' / 'MAA', asst_callback)

    run_auto_sign(current_path)

    # 启动模拟器
    execStarted = False
    while not asst.connect(
        global_config.get("adb_address", str(current_path /
                          "RuntimeComponents" / "adb" / "adb.exe")),
        global_config.get("emulator_address", '127.0.0.1:5555')
    ):
        logging.info(
            f"try to connect {global_config.get('emulator_address', '127.0.0.1:5555')}")
        if not execStarted:
            os.startfile(
                r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\MuMuPlayer.exe")
            logging.info(
                r"started emulator at C:\Program Files\Netease\MuMuPlayer-12.0\shell\MuMuPlayer.exe")
            execStarted = True
        time.sleep(2)

    time.sleep(10)
    for person in personal_config:
        time.sleep(3)
        run_personal_scht_tasks(asst, global_config, person)

    logging.info(f"everything completed.exit")
