import os
import pathlib
import sys
import logging
import threading
import var

from Libs.scheduler import start_scheduler
from Libs.utils import read_config_and_validate, get_logging_handlers
from Libs.maa_runner import run_all_devs
from Libs.test import test

var.cli_env = pathlib.Path(__file__, "../")
var.asst_res_lib_env = var.cli_env / "RuntimeComponents" / "MAA"
var.lock = {'list': threading.Lock(), 'asst': threading.Lock()}
var.global_config = read_config_and_validate("global")
var.personal_configs = read_config_and_validate("personal")
var.verbose = "-v" in sys.argv or "--verbose" in sys.argv
var.tasks = []

try:
    os.remove(str(var.cli_env / "Log" / "log.log"))
    os.remove(str(var.asst_res_lib_env / "debug" / "asst.log"))
except:
    pass

logging.basicConfig(level=logging.DEBUG,
                    handlers=get_logging_handlers(
                        logging.DEBUG, logging.DEBUG if var.verbose else logging.INFO),
                    format="%(asctime)s[%(levelname)s] %(message)s")
logging.info(f"started up at {var.cli_env}")
logging.info(f"with global config {var.global_config}")
logging.info(f"with personal config {var.personal_configs}")

def main():
    start_scheduler()
    logging.info(f"everything completed. exit")

if __name__ == "__main__":
    if "-t" in sys.argv:
        test()
    elif "scht" in sys.argv:
        main()
    elif "run" in sys.argv:
        run_all_devs()