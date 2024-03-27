import var
from Libs.utils import *
from Libs.test import test
from Libs.maa_runner import run

mode = init(main_path=__file__)

if __name__ == '__main__':
    logging.info(f'CLI started up at {var.cli_env}')
    logging.debug(f'With MAA {var.maa_env}')
    logging.debug(f'With global config {var.global_config}')
    logging.debug(f'With config templates {var.config_templates}')
    logging.debug(f'With personal config {var.personal_configs}')

    try:
        if entrance := locals().get(mode, None):
            if var.verbose and False:
                profile = LineProfiler(entrance)
                profile.runcall(entrance)
                profile.print_stats()
            else:
                entrance()

        logging.info(f'CLI ready to exit')

    except Exception as e:
        logging.critical(f'An unexpected error was occured when running: {e}', exc_info=True)
