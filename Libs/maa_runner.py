from ast import List
from socket import AI_PASSIVE
from wsgiref.headers import tspecials
from jax import devices
from pyparsing import opAssoc
from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_callback, asst_tostr, load_res, update_nav
from Libs.utils import kill_processes_by_name, read_config_and_validate, read_json
import var

import threading
import asyncio
import logging
import os
import time
import pathlib
import copy


async def run_all_devs():
    update_nav()

    var.task_and_device_manager._tasks = {}
    var.personal_configs = read_config_and_validate("personal")
    personal_default = read_json(
        var.cli_env / "Libs" / "json" / "default" / "personal.json")
    for personal_config in var.personal_configs:
        var.task_and_device_manager.add_task(
            extend_full_tasks(personal_config, personal_default))
        pass

    load_res(None)

    for process in var.global_config['devices']:
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)

    for dev in var.global_config["devices"]:
        var.task_and_device_manager.add_device(Dev(dev))

    var.task_and_device_manager.monitor()

    for process in var.global_config['devices']:
        for process_name in process['process_name']:
            kill_processes_by_name(process_name)


def extend_full_tasks(config, defaults):
    return_ls: list = []

    tasks = config["task"]
    for default_task in defaults:
        default_task: dict

        fin_task_config = copy.deepcopy(default_task["task_config"])
        fin_task_name = copy.deepcopy(default_task["task_name"])

        fin_task_config.update(tasks.get(fin_task_name, {}))
        if fin_task_name not in config.get("blacklist", []):
            return_ls.append({
                "task_name": fin_task_name,
                "task_config": fin_task_config
            })

            # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
            if fin_task_name == "StartUp":
                if fin_task_config.get("account_name", "") != "":
                    another_startup_task_config = copy.deepcopy(
                        fin_task_config)
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


class Dev:
    def __init__(self, dev_config) -> None:
        self._adb_path = os.path.abspath(dev_config["adb_path"])
        self._start_path = dev_config["start_path"]

        self.emulator_addr = dev_config["emulator_address"]
        self.running_task = None

        self._connected = False

        self._asst = Asst(asst_callback)
        self._asst_str = asst_tostr(self.emulator_addr)

        if not self._connected:
            _execStart = False
            while True:

                logging.debug(
                    f"{self._asst_str} try to connect {self.emulator_addr}")

                if self._asst.connect(self._adb_path, self.emulator_addr):
                    logging.debug(
                        f"{self._asst_str} connected {self.emulator_addr}")
                    break

                # 启动模拟器
                if not _execStart and self._start_path is not None:
                    os.startfile(os.path.abspath(
                        self._start_path))  # 程序结束后会自动关闭？！
                    _execStart = True

                    logging.debug(f"started emulator at {self._start_path}")

                time.sleep(2)

            # time.sleep(15)
            self._connected = True
        pass

    def run_task(self, task):

        add_personal_tasks(self._asst, task)

        max_wait_time = 50*60

        self._asst.start()

        logging.info(f"{self._asst_str} done task {task}")


class TaskAndDeviceManager:
    _devices: list[Dev] = []
    _tasks = {}

    def add_device(self, device):
        self._devices.append(device)
        pass

    def add_task(self, task):
        server = [
            maa_task
            for maa_task in task["task"]
            if maa_task["task_name"] == "StartUp"
        ][0]["task_config"]["client_type"]
        if server == "Bilibili":
            server = "Official"

        server_tasks_ls = self._tasks.get(server)
        if server_tasks_ls is None:
            self._tasks[server] = [task]
        else:
            self._tasks[server].append(task)

    def monitor(self):
        while (True):
            if len(self._tasks) != 0:
                first_key = next(iter(self._tasks.keys()))
                task_list = self._tasks[first_key]
                idle_devs = [
                    dev for dev in self._devices if not dev._asst.running()]
                for dev in idle_devs:
                    run_task = None

                    for_this_aval_tasks_matches_addr = [
                        task for task in task_list if task.get('device') == dev.emulator_addr]
                    if len(for_this_aval_tasks_matches_addr) == 0:
                        for_this_aval_tasks = [
                            task for task in task_list if task.get('device') == None]
                        if len(for_this_aval_tasks) == 0:
                            pass
                        else:
                            run_task = for_this_aval_tasks[0]
                    else:
                        run_task = for_this_aval_tasks_matches_addr[0]
                        pass

                    if run_task is not None:
                        dev.run_task(run_task)
                        task_list.remove(run_task)
                        pass

                all_dev_is_idle = all(not device._asst.running()
                                      for device in self._devices)
                if all_dev_is_idle:
                    self._tasks.pop(first_key)
                    first_key = next(iter(self._tasks.keys()))
                    load_res(first_key)
                    pass
            else:
                break

            time.sleep(2)
            pass
    pass
