import json
import logging
from Libs.MAA.asst.asst import Asst
from Libs.MAA.asst.utils import Message


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
