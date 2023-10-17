import json
from RuntimeComponents.MAA.Python.asst.asst import Asst
from RuntimeComponents.MAA.Python.asst.utils import Message

@Asst.CallBackType
def asst_callback(msg, details, arg):
    m = Message(msg)
    d = json.loads(details.decode('utf-8'))

    print(m, d, arg)