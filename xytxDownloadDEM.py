#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    :2025/04/19 19:54:28
# @Author  :小 y 同 学
# @公众号   :小y只会写bug
# @CSDN    :https://blog.csdn.net/weixin_64989228?type=blog
# @Discript: 批量下载SRTMGL1 DEM数据产品，DEM网站：http://step.esa.int/auxdata/dem/SRTMGL1

import argparse
import os
import shutil
import requests
from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import sys

console = Console()
progress = Progress(
    TextColumn("[bold blue] {task.fields[filename]}", justify="right"),
    BarColumn(
        bar_width=20,
        style="white",
        complete_style="bold magenta",
        finished_style="bold green",
    ),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    DownloadColumn(),
    "•",
    TransferSpeedColumn(),
    "•",
    TimeRemainingColumn(),
)


class LonLat:
    """经纬度类，用以存储经纬度信息，
    其中经度为(-180,180),其中0为E000；
    纬度为(-90,90),S为-,N为+,0为N00"""

    def __init__(self, lonInt: int, latInt: int):
        self.lonInt = lonInt  # (-180,180),其中0为E000
        self.latInt = latInt  # (-90,90),S为-,N为+,0为N00

    def getStr(self):
        """获取一个带WESN字母的经纬度字符串"""
        return (
            f"{'W' if self.lonInt < 0 else 'E'}{str(abs(self.lonInt)).rjust(3, '0')}",
            f"{'S' if self.latInt < 0 else 'N'}{str(abs(self.latInt)).rjust(2, '0')}",
        )


def log_ok(message: str):
    now = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    console.print(f"[bold green] {now} {message}")


def singleDEMDown(*args):
    """
    下载单个DEM数据产品
    :param url: DEM的url地址
    :param saveFolder: 保存的文件夹，注意不要带文件名，None则表示放到项目目录下
    :param ipPort: ip代理端口参数，None则表示不使用代理
    :return: None
    """
    url, saveFolder, ipPort, task_id = args
    proxies = {"http://": ipPort, "https://": ipPort} if ipPort else None

    fileName = url.split("/")[-1]

    filePath = fileName
    if saveFolder:
        filePath = os.path.join(saveFolder, fileName)
    tempfilePath = filePath + ".temp"

    if os.path.exists(filePath):
        console.print(
            f"[bold magenta] {os.path.basename(filePath)} 文件已存在[/] — [green]跳过下载[/green]"
        )
        return True
    try:
        res = requests.get(url=url, stream=True, proxies=proxies, timeout=20)
        if res.status_code == 200:
            data_size = round(float(res.headers["Content-Length"]))
            task_id = progress.add_task(
                "download",
                filename=os.path.basename(filePath),
                total=data_size,
                start=False,
            )
            progress.start_task(task_id)
            with open(tempfilePath, mode="wb") as f:
                for chunk in res.iter_content(chunk_size=1024 * 1024):
                    f.write(chunk)
                    progress.update(task_id, advance=len(chunk))
            shutil.move(tempfilePath, filePath)
            res.close()
            return True
        else:
            raise ValueError("status!=200")

    except:
        singleDEMDown(url, saveFolder, ipPort)


def createLonLat(minRange: LonLat, maxRange: LonLat):
    lls = []
    for i in range(minRange.lonInt, maxRange.lonInt + 1):
        for j in range(minRange.latInt, maxRange.latInt + 1):
            lls.append(LonLat(i, j))
    return lls


def saveList(myList: list, savePath) -> None:
    with open(savePath, mode="w") as f:
        f.write("\n".join(myList))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="多进程DEM数据下载脚本,代理已经内置\n（数据来源:https://step.esa.int/auxdata/dem/SRTMGL1/）\n Created by xytx",
        epilog="Example: xytxDownloadDEM.py 107 110 28 30",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("w", type=float, help="经度西界")
    parser.add_argument("e", type=float, help="经度东界")
    parser.add_argument("s", type=float, help="纬度南界")
    parser.add_argument("n", type=float, help="纬度北界")
    args = parser.parse_args()

    # 参数配置
    w = int(sys.argv[1])
    e = int(sys.argv[2])
    s = int(sys.argv[3])
    n = int(sys.argv[4])
    min_range = LonLat(w, s)
    max_range = LonLat(e, n)
    IPPort = "127.0.0.1:10086"  # todo 设置代理
    saveFolder = "."  # todo 设置保存文件夹

    # ----------------------------------------------
    if os.path.exists(saveFolder) is False:
        os.makedirs(saveFolder)

    cmdfile = "stitchDem.sh"
    cmd = f"dem.py -k -f -a stitch -b {min_range.latInt} {max_range.latInt} {min_range.lonInt} {max_range.lonInt} -r -s 1 -c"
    with open(os.path.join(saveFolder, cmdfile), "w") as f:
        f.write(cmd)

    proxies = {"http": IPPort, "https": IPPort} if IPPort else None
    log_ok("开始获取dem下载链接")
    result = requests.get("https://step.esa.int/auxdata/dem/SRTMGL1/", proxies=proxies)

    lls = createLonLat(min_range, max_range)  # 创建一系列经纬度表
    urls = []
    for ll in lls:
        name = f"{ll.getStr()[1]}{ll.getStr()[0]}.SRTMGL1.hgt.zip"
        if name in result.text:
            urls.append(f"http://step.esa.int/auxdata/dem/SRTMGL1/{name}")

    savePath = os.path.join(
        saveFolder,
        f"{''.join(min_range.getStr())}-{''.join(max_range.getStr())}.txt",
    )

    saveList(urls, savePath)  # todo 保存url表
    log_ok(f"{os.path.basename(savePath)},dem下载连接已保存！")
    log_ok(f"开始下载dem数据,预计需要下载{len(urls)}个文件")

    # =====>2025/07/31 17:52:40 单线程下载 <=====
    # for i, url in enumerate(urls):
    #     print(url)
    #     # os.system(f"wget -P {saveFolder} {url}")  # todo 使用wget下载
    # singleDEMDown(url, saveFolder, IPPort, i)  # 使用脚本下载

    # =====> 多进程下载 <=====
    with progress:
        with ThreadPoolExecutor(max_workers=10) as executor:  # prin
            future_to_url = {
                executor.submit(singleDEMDown, url, saveFolder, IPPort, i): url
                for i, url in enumerate(urls)
            }
            for future in future_to_url:
                future.result()  # 等待所有下载任务完成

    log_ok("dem下载完成,dem.py拼接命令（两条都可以）：")
    console.print(f"{cmd}")
    console.print(f"bash {cmdfile}")
