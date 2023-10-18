import subprocess
import os
import logging


def run_auto_sign(current_path):
    logging.info("skland auto sign started, the following is the output of the program:")

    # 使用subprocess运行，并将标准输出重定向到PIPE
    process = subprocess.Popen(["python", str(current_path / 'RuntimeComponents' / 'skylandautosign' / 'skyland.py')],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=str(current_path / 'RuntimeComponents' / 'skylandautosign'))

    for line in iter(process.stdout.readline, b''):
        logging.info(line.strip().decode('utf-8'))
    process.wait()

    logging.info("skland auto sign exited")
