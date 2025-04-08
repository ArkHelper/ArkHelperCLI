# EvATive7 forked from github.com/TanyaShue/MaaYYs
# Copyright: TanyaShue

import argparse
import os
import shutil
import sys
import zipfile

import PyInstaller.__main__

parser = argparse.ArgumentParser()
# parser.add_argument( "--version", type=str, help="Specify the version of the script", default="none")
parser.add_argument(
    "--os",
    type=str,
    help="Specify the operating system on which the building is running",
    default="none",
)
parser.add_argument(
    "--arch",
    type=str,
    help="Specify the arch on which the building is running",
    default="none",
)
args = parser.parse_args()
ZIP_FILENAME = f"akhcli_{args.os}_{args.arch}.zip"


# 获取当前工作目录
current_dir = os.getcwd()


# 复制 assets 文件夹到 dist 目录
dist_dir = os.path.join(current_dir, "dist")

# 如果目标路径存在，先删除它
if os.path.exists(dist_dir):
    shutil.rmtree(dist_dir)

# 运行 PyInstaller 打包命令
command = [
    "src/main.py",
    "--onefile",
    "--name=akhcli.exe",
    # "--clean",
]
if sys.platform == "win32":
    command.append(
        f'--add-binary={os.path.join(current_dir, "misc", "windows", "dll", "msvcp140.dll")}{os.pathsep}.'
    )
    command.append(
        f'--add-binary={os.path.join(current_dir, "misc", "windows", "dll", "vcruntime140.dll")}{os.pathsep}.'
    )

print(" ".join(command))
PyInstaller.__main__.run(command)


# 压缩 dist 文件夹为 zip 文件，并保存在 dist 目录中
zip_filepath = os.path.join(dist_dir, ZIP_FILENAME)

with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            # 获取文件的绝对路径并相对路径
            file_path = os.path.join(root, file)
            # 跳过刚生成的压缩包
            if file == ZIP_FILENAME:
                continue
            arcname = os.path.relpath(file_path, dist_dir)
            zipf.write(file_path, arcname)

# 删除 dist 文件夹中的所有文件和文件夹，保留压缩包
for root, dirs, files in os.walk(dist_dir):
    for file in files:
        file_path = os.path.join(root, file)
        # 不删除生成的压缩包
        if file != ZIP_FILENAME:
            os.remove(file_path)
    for dir in dirs:
        shutil.rmtree(os.path.join(root, dir), ignore_errors=True)

print(f"Packaging and compression completed: {zip_filepath}")
