import json
import pathlib
import time
import os

from RuntimeComponents.MAA.Python.asst.asst import Asst
from RuntimeComponents.MAA.Python.asst.utils import Message, Version, InstanceOptionType
from RuntimeComponents.MAA.Python.asst.updater import Updater
from RuntimeComponents.MAA.Python.asst.emulator import Bluestacks

from Libs.maa_personal_scht_runner import run_personal_scht_tasks
from Libs.maa_util import asst_callback
from Libs.maa_initer import init
from Libs.utils import read_config


if __name__ == "__main__":

    # 存放 dll 文件及资源的路径
    current_path = pathlib.Path(__file__, "../")
    global_config = read_config(current_path, 'global')
    personal_config = read_config(current_path, 'personal')

    asst = init(current_path / 'RuntimeComponents' / 'MAA', asst_callback)

    # 启动模拟器
    execStarted = False
    while not asst.connect(
        global_config.get("adb_address", str(current_path /
                          "RuntimeComponents" / "adb" / "adb.exe")),
        global_config.get("emulator_address", '127.0.0.1:5555')
    ):
        if not execStarted:
            os.startfile(
                r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\MuMuPlayer.exe")
            execStarted = True
        time.sleep(2)

    for person in personal_config:
        time.sleep(3)
        run_personal_scht_tasks(asst, global_config, person)
