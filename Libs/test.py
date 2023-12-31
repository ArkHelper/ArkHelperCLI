import time
import os
import var
from Libs.maa_runner import Device
from Libs.maa_util import update_nav, load_res
from Libs.maa_runner import run_all_devs


def test():
    try:
        os.remove(str(var.cli_env / 'Log' / 'log.log'))
        os.remove(str(var.asst_res_lib_env / 'debug' / 'asst.log'))
    except:
        pass

    dev = Device({
        'emulator_address': '127.0.0.1:16416',
        'adb_path': './RuntimeComponents/adb/adb.exe',
        'start_path': 'C:\\Program Files\\Netease\\MuMuPlayer-12.0\\shell\\MuMuPlayer.exe',
        'process_name': [
            'MuMuVMMHeadless',
            'MuMuPlayer'
        ]
    }, {}, {
        'index': 1
    })
    load_res(dev._asst)
    load_res(dev._asst, 'YoStarJP')
    load_res(dev._asst, 'YoStarEN')
    dev.connect()

    dev._asst.append_task('Recruit',{
        'refresh': True,
        'force_refresh': True,
        'select': [
            4,
            5
        ],
        'confirm': [
            3,
            4,
            5
        ],
        'times': 4,
        'set_time': True,
        'expedite': False,
        'expedite_times': 3,
        'skip_robot': False,
        'recruitment_time': {
            '3': 460
        },
        'report_to_penguin': False,
        'report_to_yituliu': False,
        'penguin_id': '',
        'server': 'CN'

    })
    dev._asst.start()
    time.sleep(10000)
    pass
