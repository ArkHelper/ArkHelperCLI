from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message, Version, InstanceOptionType

import ctypes
import pathlib
import logging


def init(path):
    # Updater(path, Version.Stable).update()

    # 加载 dll 及资源
    #
    # incremental_path 参数表示增量资源所在路径。两种用法举例：
    # 1. 传入外服的增量资源路径：
    #     Asst.load(path=path, incremental_path=path / 'resource' / 'global' / 'YoStarEN')
    # 2. 加载活动关导航（需额外下载）：
    # 下载活动关导航
    #import urllib.request
    #ota_tasks_url = 'https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json'
    #ota_tasks_path = path / 'cache' / 'resource' / 'tasks.json'
    #ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
    #with open(ota_tasks_path, 'w', encoding='utf-8') as f:
    #    with urllib.request.urlopen(ota_tasks_url) as u:
    #        f.write(u.read().decode('utf-8'))
#
    #logging.info(f"asst tasks uploaded")

    # 加载
    Asst.load(path=path, incremental_path=path /
              'resource' / 'global' / 'YoStarEN')
    Asst.load(path=path, incremental_path=path / 'cache')
    Asst.load(path=path)

    logging.info(f"asst resource and lib loaded")
