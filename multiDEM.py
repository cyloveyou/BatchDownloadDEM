# -*- coding: utf-8 -*-
# @Time    :2024/3/8 17:01
# @Author  :小 y 同 学
# @公众号   :小y只会写bug
# @CSDN    :https://blog.csdn.net/weixin_64989228?type=blog
import os.path
import shutil
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


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


def singleDEMDown(url, saveFolder=None, ipPort=None):
    """
    下载单个DEM数据产品
    :param url: DEM的url地址
    :param saveFolder: 保存的文件夹，注意不要带文件名，None则表示放到项目目录下
    :param ipPort: ip代理端口参数，None则表示不使用代理
    :return: 下载的文件路径
    """
    proxies = {"http://": ipPort, "https://": ipPort} if ipPort else None

    fileName = url.split("/")[-1]

    filePath = fileName
    if saveFolder:
        filePath = os.path.join(saveFolder, fileName)
    tempfilePath = filePath + ".temp"

    if os.path.exists(filePath):
        print(f"{filePath}文件已存在，跳过下载")
        return filePath
    try:
        res = requests.get(url=url, stream=True, proxies=proxies)
        if res.status_code == 200:
            data_size = round(float(res.headers["Content-Length"])) / 1024 / 1024
            with open(tempfilePath, mode="wb") as f:
                for data in tqdm(
                    iterable=res.iter_content(1024 * 1024),
                    total=int(data_size),
                    desc=tempfilePath,
                    unit="MB",
                ):
                    f.write(data)
            shutil.move(tempfilePath, filePath)
            print(f"{filePath}===下载完成")
            res.close()
            return filePath
        else:
            raise ValueError("status!=200")

    except Exception as e:
        print(f"下载 {url} 失败: {e}")
        return None


def createLonLat(minRange: LonLat, maxRange: LonLat):
    lls = []
    for i in range(minRange.lonInt, maxRange.lonInt + 1):
        for j in range(minRange.latInt, maxRange.latInt + 1):
            lls.append(LonLat(i, j))
    return lls


def saveList(myList: list, savePath) -> None:
    with open(savePath, mode="w") as f:
        f.write("\n".join(myList))
        print(f"{savePath}---写入完成！")


if __name__ == "__main__":
    # 参数配置
    min_range = LonLat(101, 27)  # 设置经度最小和纬度最小
    max_range = LonLat(107, 33)  # 设置经度最大和纬度最大
    IPPort = "127.0.0.1:10086"  # 设置代理
    saveFolder = "."  # 设置保存文件夹

    # ----------------------------------------------
    if not os.path.exists(saveFolder):
        os.makedirs(saveFolder)

    cmd = f"dem.py -k -f -a stitch -b {min_range.latInt} {max_range.latInt} {min_range.lonInt} {max_range.lonInt} -r -s 1 -c"
    with open(os.path.join(saveFolder, "stitchDem.sh"), "w") as f:
        f.write(cmd)

    proxies = {"http://": IPPort, "https://": IPPort} if IPPort else None

    print("开始获取下载链接")
    result = requests.get("https://step.esa.int/auxdata/dem/SRTMGL1/", proxies=proxies)

    lls = createLonLat(min_range, max_range)  # 创建一系列经纬度表
    urls = []
    for ll in lls:
        name = f"{ll.getStr()[1]}{ll.getStr()[0]}.SRTMGL1.hgt.zip"
        if name in result.text:
            urls.append(f"http://step.esa.int/auxdata/dem/SRTMGL1/{name}")

    saveList(
        urls,
        os.path.join(
            saveFolder,
            f"{''.join(min_range.getStr())}-{''.join(max_range.getStr())}.txt",
        ),
    )  # 保存url表
    print(f"开始下载，预计需要下载{len(urls)}个文件")

    # 使用ThreadPoolExecutor进行多线程下载
    with ThreadPoolExecutor(max_workers=10) as executor:  # 你可以根据需要调整max_workers的数量
        future_to_url = {executor.submit(singleDEMDown, url, saveFolder, IPPort): url for url in urls}
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                future.result()  # 这将引发异常，如果线程中的任务引发了异常
            except Exception as exc:
                print(f"{url} 生成异常: {exc}")

    print("拼接命令：")
    print(cmd)