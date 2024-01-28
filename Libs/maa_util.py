import requests
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message, Version, InstanceOptionType
from Libs.utils import read_json, read_yaml, write_json, read_file, write_file
import var

import pathlib
import os
import logging
import json
from typing import Union, Optional


def asst_tostr(emulator_address):
    return f'asst instance({emulator_address})'


def load_res(asst: Asst, client_type: Optional[Union[str, None]] = None):
    incr: pathlib.Path
    if client_type in ['Official', 'Bilibili', None]:
        incr = var.asst_res_lib_env / 'cache'
    else:
        incr = var.asst_res_lib_env / 'resource' / 'global' / str(client_type)

    logging.debug(f'asst resource and lib loaded from incremental path {incr}')
    asst.load_res(incr)


def update_nav():
    path = var.asst_res_lib_env

    need_update = False

    last_update_time_file_server = 'https://ota.maa.plus/MaaAssistantArknights/api/lastUpdateTime.json'
    last_update_time_file_local = path / 'cache' / 'resource' / 'lastUpdateTime.json'
    try:
        last_update_time_local = read_json(last_update_time_file_local)['timestamp']
    except:
        last_update_time_file_local.parent.mkdir(parents=True, exist_ok=True)
        write_file(last_update_time_file_local, '')
        last_update_time_local = 0

    last_update_time_content_server = requests.get(last_update_time_file_server).content
    last_update_time_server = json.loads(last_update_time_content_server)['timestamp']

    if last_update_time_local < last_update_time_server:
        need_update = True

    logging.debug(f'tasks resource last update time is {last_update_time_local} and the data on server is {last_update_time_server}. need to update is {need_update}')

    if need_update:
        ota_tasks_url = 'https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json'
        ota_tasks_path = path / 'cache' / 'resource' / 'tasks.json'
        
        ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
        write_file(ota_tasks_path, requests.get(ota_tasks_url).content.decode('utf-8'))
        logging.debug(f'asst tasks updated')

        write_file(last_update_time_file_local, last_update_time_content_server.decode('utf-8'))
        logging.debug(f'last update time updated')

    pass
