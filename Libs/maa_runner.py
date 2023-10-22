from Libs.MAA.asst.asst import Asst
from Libs.maa_util import asst_callback, asst_tostr, load_res
import var

import threading
import asyncio
import logging
import os
import time
import pathlib


async def run_all_tasks():
    async_enabled = False

    if async_enabled:
        async_task_ls = []
        for dev in var.global_config["devices"]:
            task = asyncio.to_thread(
                run_task_per_dev, dev)
            async_task_ls.append(task)
        await asyncio.gather(*async_task_ls)
    else:
        for dev in var.global_config["devices"]:
            run_task_per_dev(dev)

    # kill_processes_by_name("MuMuVMMHeadless.exe")


def add_personal_tasks(asst, config):
    logging.info(
        f'started scht task with user {config.get("client_type", "Official")}:{config.get("account_name", "")}')
    asst.append_task('StartUp', {
        "enable": True,
        "client_type": config.get("client_type", 'Official'),
        "start_game_enabled": True,
        "account_name": config.get("account_name", '')
    })
    # MAA的一个bug，有概率切换账号后无法登录，所以再加个登录Task
    if config.get("account_name", '') != '':
        asst.append_task('StartUp', {
            "enable": True,
            "client_type": config.get("client_type", 'Official'),
            "start_game_enabled": True,
            "account_name": ''
        })
    asst.append_task('Fight', {
        'enable': True,
        'stage': config.get('stage', ''),
        'medicine': 0,
        'expiring_medicine': 0,
        'stone': 0,
        'times': 2147483647,
        'drops': {},
        'report_to_penguin': False,
        'penguin_id': '',
        'server': 'CN',
        'client_type': '',
        'DrGrandet': False
    })
    asst.append_task('Infrast', {
        'facility': [
            'Mfg',
            'Trade',
            'Control',
            'Power',
            'Reception',
            'Office',
            'Dorm',
            'Processing'
        ],
        'drones': config.get('drones', 'PureGold'),
        'threshold': 0.2,
        'dorm_notstationed_enabled': True,
        'dorm_trust_enabled': True,
        'replenish': True,
        'mode': 0,
        'filename': '',
        'plan_index': 0
    })
    asst.append_task('Recruit', {
        'refresh': True,
        'force_refresh': True,
        'select': [
            4
        ],
        'confirm': [
            3,
            4
        ],
        'times': 3,
        'set_time': True,
        'expedite': False,
        'expedite_times': 3,
        'skip_robot': True,
        'recruitment_time': {
            '3': 460
        },
        'report_to_penguin': True,
        'report_to_yituliu': True,
        'penguin_id': '',
        'server': 'CN'
    })
    asst.append_task('Mall', {
        'credit_fight': False,
        'shopping': True,
        'buy_first': [
            '招聘许可',
            '固源岩',
            '源岩',
            '装置'
        ],
        'blacklist': [
            '加急许可'
        ],
        'force_shopping_if_credit_full': True
    })
    asst.append_task('Award', {
        'award': True,
        'mail': True
    })


def run_task_per_dev(dev):

    def get_aval_task():
        def search_ls(match):
            return [
                pc
                for pc in var.personal_configs
                if pc.get("device") == match
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
        current_task_personal_config = get_aval_task()
        if current_task_personal_config is None:
            break

        with list_lock:
            var.personal_configs.remove(current_task_personal_config)

        load_res(current_task_personal_config["client_type"])

        if asst is None:
            asst = Asst(asst_callback)
            asst_str = asst_tostr(emulator_addr)

            logging.debug(f"{asst_str} inited")

        logging.debug(
            f"{asst_str} got task {current_task_personal_config}")

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

        add_personal_tasks(asst, current_task_personal_config)

        asst.start()
        while True:
            if not asst.running():
                break
            time.sleep(5)

    logging.info(
        f"{asst_str} done all available tasks and this thread will safely exit")
