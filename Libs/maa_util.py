from typing import Union, Optional
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message, Version, InstanceOptionType
import var

import pathlib
import logging
import json
import logging


@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        d = json.loads(details.decode('utf-8'))
        logging.debug(f'got callback from asst inst: {m},{arg},{d}')
    except:
        pass


def asst_tostr(emulator_address):
    return f"asst instance({emulator_address})"


def load_res(client_type: Optional[Union[str, None]] = None):
    if client_type in ["Official", "Bilibili", None]:
        Asst.load(var.asst_res_lib_env)

        logging.debug(f"asst resource and lib loaded from {var.asst_res_lib_env}")
    else:
        incr = var.asst_res_lib_env / 'resource' / 'global' / str(client_type)
        Asst.load(var.asst_res_lib_env, incr)

        logging.debug(f"asst resource and lib loaded from {var.asst_res_lib_env} and {incr}")



def update(path):  # FIXME
    # Updater(path, Version.Stable).update()

    # 加载 dll 及资源
    #
    # incremental_path 参数表示增量资源所在路径。两种用法举例：
    # 1. 传入外服的增量资源路径：
    #     Asst.load(path=path, incremental_path=path / 'resource' / 'global' / 'YoStarEN')
    # 2. 加载活动关导航（需额外下载）：
    # 下载活动关导航
    # import urllib.request
    # ota_tasks_url = 'https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json'
    # ota_tasks_path = path / 'cache' / 'resource' / 'tasks.json'
    # ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
    # with open(ota_tasks_path, 'w', encoding='utf-8') as f:
    #    with urllib.request.urlopen(ota_tasks_url) as u:
    #        f.write(u.read().decode('utf-8'))
    #
    # logging.info(f"asst tasks uploaded")
    pass
