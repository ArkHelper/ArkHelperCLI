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
var.global_config = read_config('global')
var.personal_configs = read_config('personal')
var.default_personal_config = read_config('default_personal')
var.maa_env = pathlib.Path(var.global_config['maa_path'])
var.verbose = verbose

fix_log_file()

logging.basicConfig(level=logging.DEBUG,
                    handlers=get_logging_handlers(),
                    format='%(asctime)s[%(levelname)s][%(name)s] %(message)s')

if __name__ == '__main__':
    logging.debug(f'Started up at {var.cli_env}.')
    logging.debug(f'With global config {var.global_config}.')
    logging.debug(f'With personal config {var.personal_configs}.')
    
    try:
        if mode == 'test':
            test()
        elif mode == 'run':
            run()

    except Exception as e:
        logging.error(f"An unexpected error was occured when running: {e}", exc_info=True)
