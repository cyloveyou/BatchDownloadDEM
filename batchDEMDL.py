# -*- coding: utf-8 -*-
# @Time    :2024/3/8 17:01
# @Author  :小 y 同 学
# @公众号   :小y只会写bug
# @CSDN    :https://blog.csdn.net/weixin_64989228?type=blog
import os.path
import shutil
import requests
from tqdm import tqdm


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
    :return: None
    """
    proxies = {"http://": ipPort, "https://": ipPort} if ipPort else None

    fileName = url.split("/")[-1]

    filePath = fileName
    if saveFolder:
        filePath = os.path.join(saveFolder, fileName)
    tempfilePath = filePath + ".temp"

    if os.path.exists(filePath):
        print(f"{filePath}文件已存在，跳过下载")
        return True
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
        print(f"{savePath}---写入完成！")


if __name__ == "__main__":
    # 参数配置
    min_range = LonLat(115, 22)  # todo 设置经度最小和纬度最小
    max_range = LonLat(119, 27)  # todo 设置经度最大和纬度最大
    IPPort = "127.0.0.1:7897"  # todo 设置代理
    saveFolder = "./Guangdong"  # todo 设置保存文件夹

    # ----------------------------------------------
    if os.path.exists(saveFolder) is False:
        os.makedirs(saveFolder)

    cmd = f"dem.py -k -f -a stitch -b {min_range.latInt} {max_range.latInt} {min_range.lonInt} {max_range.lonInt} -r -s 1 -c"
    with open(os.path.join(saveFolder, "stitchDem.sh"), "w") as f:
        f.write(cmd)

    proxies = {"http://": IPPort, "https://": IPPort} if IPPort else None
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
    )  # todo 保存url表
    print(f"开始下载，预计需要下载{len(urls)}个文件")
    count = 0
    for url in urls:
        print(url)
        # os.system(f"wget -P {saveFolder} {url}")  # todo 使用wget下载
        singleDEMDown(url, saveFolder, IPPort)  # 使用脚本下载
    print("拼接命令：")
    print(cmd)
