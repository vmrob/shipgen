import random

import ConfigFile

dists = {}


class Distribution:
	def __init__(self, probs):
		self.probabilities = [min(max(p, 0), 1) for p in probs]
		if ((not self.probabilities) or (self.probabilities[-1] >= 1)):
			self.probabilities.append(0)

	def getCount(self):
		count = 0
		prob = 0
		while (True):
			if (count < len(self.probabilities)):
				prob = self.probabilities[count]
			if (random.random() < prob):
				count += 1
			else:
				return count


def init():
	configDict = ConfigFile.read_config("dists.json")
	for distName in configDict.keys():
		probs = [float(x) for x in configDict[distName].split() if x]
		if (not probs):
			continue
		dists[distName] = Distribution(probs)


init()
