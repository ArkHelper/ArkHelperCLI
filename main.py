from datetime import datetime
import pathlib
import logging
import var

from Libs.utils import fix_log_file,read_config, get_logging_handlers, parse_arg
from Libs.maa_runner import run
from Libs.test import test

mode, verbose = parse_arg()

var.start_time = datetime.now()
var.cli_env = pathlib.Path(__file__, '../')
var.asst_res_lib_env = var.cli_env / 'RuntimeComponents' / 'MAA'
var.global_config = read_config('global')
var.personal_configs = read_config('personal')
var.default_personal_config = read_config('default_personal')
var.verbose = verbose

fix_log_file()

logging.basicConfig(level=logging.DEBUG,
                    handlers=get_logging_handlers(logging.DEBUG, logging.DEBUG if var.verbose else logging.INFO),
                    format='%(asctime)s[%(levelname)s] %(message)s')

if __name__ == '__main__':
    logging.debug(f'started up at {var.cli_env}')
    logging.debug(f'with global config {var.global_config}')
    logging.debug(f'with personal config {var.personal_configs}')
    
    try:
        if mode == 'test':
            test()
        elif mode == 'run':
            run()

    except Exception as e:
        logging.error(f"An expected error was occured when running:", exc_info=True)
