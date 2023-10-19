from Libs.maa_util import asst_callback, asst_tostr
from Libs.MAA.asst.asst import Asst
from Libs.maa_personal_scht_runner import add_personal_scht_tasks_to_inst

import threading
import logging
import os
import time
import pathlib


def run_and_init_asst_inst(dev, global_config, personal_config):
    lock = threading.Lock()

    adb_path = os.path.abspath(dev["adb_path"])
    start_path = dev["start_path"]
    emulator_addr = dev["emulator_address"]
    asst = Asst(asst_callback)

    connected = False

    logging.info(
        f"asst instance with device {dev['emulator_address']} inited")

    def get_aval_task():
        def search_ls(match):
            return [
                pc
                for pc in personal_config
                if pc.get("device") == match
            ]
            pass
        with lock:
            avals_in_match_device = search_ls(emulator_addr)
            if (len(avals_in_match_device) == 0):
                avals = search_ls(None)
                if (len(avals) == 0):
                    return None
                else:
                    return avals[0]
            else:
                return avals_in_match_device[0]

    while (True):
        p_config = get_aval_task()
        if p_config is None:
            break

        with lock:
            personal_config.remove(p_config)

        execStarted = False
        if not connected:
            while True:

                logging.debug(
                    f"{asst_tostr(emulator_addr)} try to connect {emulator_addr}")

                if asst.connect(adb_path, emulator_addr):
                    break

                # 启动模拟器
                if not execStarted and start_path is not None:
                    os.startfile(os.path.abspath(start_path))

                    logging.info(f"started emulator at {start_path}")

                    execStarted = True

                time.sleep(2)

        connected = True

        add_personal_scht_tasks_to_inst(asst, global_config, p_config)

        asst.start()
        while asst.running():
            time.sleep(1)

    logging.info(
        f"{asst_tostr(emulator_addr)} done all available tasks and this thread safely exit")
