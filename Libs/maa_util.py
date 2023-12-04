from math import fabs
from typing import Union, Optional

from numpy import true_divide
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message, Version, InstanceOptionType
import var

import pathlib
import os
import logging
import json
import logging
from datetime import datetime
import pytz



@Asst.CallBackType
def asst_callback(msg, details, arg):
    try:
        m = Message(msg)
        #d = json.loads(details.decode('utf-8'))
        d = details.decode('utf-8')
        logging.debug(f'got callback from asst inst: {m},{arg},{d}')
    except:
        pass


def asst_tostr(emulator_address):
    return f"asst instance({emulator_address})"


def load_res(asst:Asst, client_type: Optional[Union[str, None]] = None):
    incr:pathlib.Path
    if client_type in ["Official", "Bilibili", None]:
        incr = var.asst_res_lib_env / 'cache'
    else:
        incr = var.asst_res_lib_env / 'resource' / 'global' / str(client_type)
        
    logging.debug(f"asst resource and lib loaded from incremental path {incr}")
    asst.load_res(incr)



def update_nav(): 
    # Updater(path, Version.Stable).update() # FIXME

    import urllib.request
    path = var.asst_res_lib_env

    need_update = True

    # 测定最后一次更新时间
    last_upd_time_url = "https://ota.maa.plus/MaaAssistantArknights/api/lastUpdateTime.json"
    last_upd_time_path = path / 'cache' / 'resource' / 'lastUpdateTime.json'
    last_upd_time_path.parent.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(str(last_upd_time_path)):
        with open(str(last_upd_time_path),'w'):
            pass
    with open(last_upd_time_path, 'r+', encoding='utf-8') as f:
        with urllib.request.urlopen(last_upd_time_url) as u:
            server_json = json.loads(u.read().decode('utf-8'))
            server_time = server_json.get("timestamp")
            local_last_upd_time = 0
            try:
                local_last_upd_time_json = json.load(f)
                local_last_upd_time = local_last_upd_time_json["timestamp"]
                if local_last_upd_time >= server_time:
                    need_update = False
            except:
                pass

            logging.debug(f"tasks resource last update time is {local_last_upd_time} and the data on server is {server_time}. need to update is {need_update}")
            if (need_update):
                f.seek(0)
                f.write(json.dumps(server_json))
                f.truncate()
                logging.info(f"last update time updated")


    if need_update:
        # 下载活动关导航
        ota_tasks_url = 'https://ota.maa.plus/MaaAssistantArknights/api/resource/tasks.json'
        ota_tasks_path = path / 'cache' / 'resource' / 'tasks.json'
        ota_tasks_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ota_tasks_path, 'w', encoding='utf-8') as f:
            with urllib.request.urlopen(ota_tasks_url) as u:
                f.write(u.read().decode('utf-8'))
        logging.info(f"asst tasks updated")
        
    pass
