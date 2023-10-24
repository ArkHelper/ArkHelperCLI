from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_callback, asst_tostr, load_res, update_nav
from Libs.utils import read_config_and_validate, read_json
import var

import threading
import asyncio
import logging
import os
import time
import pathlib
import copy


async def run_all_devs():
    #update_nav()

    async_enabled = False

    if async_enabled:
        async_task_ls = []
        for dev in var.global_config["devices"]:
            task = asyncio.to_thread(
                run_tasks_by_dev, dev)
            async_task_ls.append(task)
        await asyncio.gather(*async_task_ls)
    else:
        for dev in var.global_config["devices"]:
            run_tasks_by_dev(dev)

    # kill_processes_by_name("MuMuVMMHeadless.exe")


def get_full_tasks(config, defaults):
    return_ls: list = []

    tasks = config["task"]
    for default_task in defaults:
        default_task: dict

        fin_task_config = copy.deepcopy(default_task["task_config"])
        fin_task_name = copy.deepcopy(default_task["task_name"])

        fin_task_config.update(tasks.get(fin_task_name, {}))
        return_ls.append({
            "task_name": fin_task_name,
            "task_config": fin_task_config
        })

        # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
        if fin_task_name == "StartUp":
            if fin_task_config.get("account_name", "") != "":
                another_startup_task_config = copy.deepcopy(fin_task_config)
                another_startup_task_config["account_name"] = ""
                return_ls.append({
                    "task_name": fin_task_name,
                    "task_config": another_startup_task_config
                })

    return {
        "task": return_ls,
        "device": config.get("device", None)
    }


def add_personal_tasks(asst: Asst, config):
    logging.info(
        f'append task with config {config}')
    for maa_task in config["task"]:
        asst.append_task(maa_task["task_name"], maa_task["task_config"])


def run_tasks_by_dev(dev):
    #TODO: 挪到公共位置，以适配多实例
    tasks: list = []
    var.personal_configs = read_config_and_validate("personal")
    personal_default = read_json(
        var.cli_env / "Libs" / "json" / "default" / "personal.json")
    for personal_config in var.personal_configs:
        tasks.append(get_full_tasks(personal_config, personal_default))
        pass

    def get_aval_task():
        def search_ls(matcher):
            return [
                task
                for task in tasks
                if task.get("device") == matcher
            ]
            pass
        with list_lock:
            avals_in_match_device = search_ls(emulator_addr)
            if (len(avals_in_match_device) == 0):
                avals = search_ls(None)
                if (len(avals) == 0):
                    return None
                else:
                    return avals[0]
            else:
                return avals_in_match_device[0]

    asst_lock = var.lock['asst']
    list_lock = var.lock['list']

    adb_path = os.path.abspath(dev["adb_path"])
    start_path = dev["start_path"]
    emulator_addr = dev["emulator_address"]

    connected = False
    asst = None
    asst_str = None

    while (True):
        current_task = get_aval_task()
        if current_task is None:
            break

        with list_lock:
            tasks.remove(current_task)

        load_res(
            [
                maa_task
                for maa_task in current_task["task"]
                if maa_task["task_name"] == "StartUp"
            ][0]["task_config"]["client_type"]
        )

        if asst is None:
            asst = Asst(asst_callback)
            asst_str = asst_tostr(emulator_addr)

            logging.debug(f"{asst_str} inited")

        logging.debug(
            f"{asst_str} got task {current_task}")

        if not connected:
            _execStart = False
            while True:

                logging.debug(
                    f"{asst_str} try to connect {emulator_addr}")

                if asst.connect(adb_path, emulator_addr):
                    logging.debug(f"{asst_str} connected {emulator_addr}")
                    break

                # 启动模拟器
                if not _execStart and start_path is not None:
                    os.startfile(os.path.abspath(start_path))
                    _execStart = True

                    logging.debug(f"started emulator at {start_path}")

                time.sleep(2)

        connected = True

        add_personal_tasks(asst, current_task)

        asst.start()
        while True:
            if not asst.running():
                break
            time.sleep(5)

    logging.info(
        f"{asst_str} done all available tasks and this thread will safely exit")
