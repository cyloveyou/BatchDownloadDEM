# -*- coding: utf-8 -*-
# @Time    :2024/3/8 17:01
# @Author  :小 y 同 学
# @公众号   :小y只会写bug
# @CSDN    :https://blog.csdn.net/weixin_64989228?type=blog
import copy

import requests


class LonLat:
	def __init__(self, lon: str, lat: str):
		self.lon = lon
		self.lat = lat
		self.lonInt = int(self.lon[1:])
		self.latInt = int(self.lat[1:])
		self.lonFlag = self.lon[0]
		self.latFlag = self.lat[0]


class LLMath:
	@staticmethod
	def lonAdd(ll1: LonLat, value):  # 定义自西向东为加E000->E179->W180->W001->E000
		value = value % 360  # 以360为周期
		lonValue = ll1.lonInt+value

		if lonValue>180:
			lonValue=lonValue-2*value


	@staticmethod
	def latAdd(ll2, value):  # 定义自南向北为加S90->N00->N90
		pass


def singleDEM(ll: LonLat):
	url = f"http://step.esa.int/auxdata/dem/SRTMGL1/{ll.lat}W{ll.lon}.SRTMGL1.hgt.zip"
	data = requests.get(url=url)


def createLonLat(minRange: LonLat, maxRange: LonLat):
	lls = []


# for i in range(minRange.lonInt, maxRange.lon):


if __name__ == '__main__':
	min_range = LonLat('E098', 'N23')
	max_range = LonLat('E102', 'N26')

	print(min_range.latFlag)
	x = createLonLat(min_range, max_range)
	print('2'.rjust(3, '0'))
	print(int('E098'[1:]))

	b = copy.deepcopy(min_range)
	print(id(min_range), id(b))
	print(LLMath.lonAdd(min_range, 2).lon)
