import ConfigFile

from Constants import *

MASS = 'mass'
POWER = 'power'
SIZE = 'size'
ATTACHMENTS = 'attachments'
DOORS = 'doors'
ACCESS = 'access'
ROOMS = 'rooms'


parts = {}


class Part:
	def __init__(self, configDict):
		self.mass = float(configDict.get(MASS, 0))
		self.power = float(configDict.get(POWER, 0))

		self.size = [int(x) for x in configDict.get(SIZE, "").split() if x][:3]
		self.size += [1] * (3 - len(self.size))

#####
##
		#handle attachment points (ATTACHMENTS)
		#handle cargo doors (DOORS)
		#handle access requirements (ACCESS)
##
#####

		self.rooms = {}
		for room in configDict.get(ROOMS, {}).keys():
			self.rooms[room] = float(configDict[ROOMS][room])
		# no need to normalize room affinities now; we'll do it once we know which rooms a ship has


def init():
	for size in SIZES:
		parts[size] = {}
		configDict = ConfigFile.read_config("parts_%s.json" % TYPE_ABBRS[size])
		for partName in configDict.keys():
			parts[size][partName] = Part(configDict[partName])

init()
