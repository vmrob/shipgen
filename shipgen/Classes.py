import math
import os.path
import random

import ConfigFile
import Dists
import Parts
import Rooms
import Util

from Constants import *

MATERIALS = 'materials'
ENCLOSURE = 'enclosure'
SYMMETRY = 'symmetry'
ACCEL = 'accel'
ACCEL_MIN = 'min'
ACCEL_MAX = 'max'
ACCEL_FWD = 'fwd'
ACCEL_LAT = 'lat'
TURN = 'turn'
TURN_MIN = 'min'
TURN_MAX = 'max'
POWER = 'power'
PARTS = 'parts'
PART_DISTRIBUTION = 'dist'
ROOMS = 'rooms'
ROOM_DISTRIBUTION = 'dist'

DEFAULTS = {
	MATERIALS:	"Light Armor",
	ENCLOSURE:	ENCLOSURE_FULL,
	SYMMETRY:	SYMMETRY_NONE,
	ACCEL:		{ACCEL_MIN: 1, ACCEL_MAX: 5, ACCEL_FWD: .5, ACCEL_LAT: .5},
	TURN:		{TURN_MIN: 1, TURN_MAX: 5},
	POWER:		POWER_STD,
}

THRUST_DIRECTION_COUNTS = {ACCEL: 1, ACCEL_FWD: 1, ACCEL_LAT: 4}


initialized = False
classes = {}


class ShipClass:
	def __init__(self, shipType, configDict):
		self.shipType = shipType
		self.size = TYPE_SIZES[self.shipType]
		if (self.size not in Parts.parts):
			raise Exception("No parts available for ship type %s" % self.shipType)

		materialSum = 0
		self.materials = {}
		for material in configDict.get(MATERIALS, {}).keys():
			self.materials[material] = float(configDict[MATERIALS][material])
			materialSum += self.materials[material]
		if (materialSum > 0):
			# normalize probabilities
			for material in self.materials.keys():
				self.materials[material] /= materialSum
		else:
			# no valid materials; use default
			self.materials = {DEFAULTS[MATERIALS]: 1}

		enclosureSum = 0
		self.enclosure = {}
		for encType in [ENCLOSURE_NONE, ENCLOSURE_PLATFORM, ENCLOSURE_FULL, ENCLOSURE_SEALED]:
			self.enclosure[encType] = float(configDict.get(ENCLOSURE, {}).get(encType, 0))
			enclosureSum += self.enclosure[encType]
		if (enclosureSum > 0):
			# normalize probabilities
			for encType in self.enclosure.keys():
				self.enclosure[encType] /= enclosureSum
		else:
			# no valid enclosure types; use default
			self.enclosure = {DEFAULTS[ENCLOSURE]: 1}

		symmetrySum = 0
		self.symmetry = {}
		for symType in [SYMMETRY_NONE, SYMMETRY_PARTIAL, SYMMETRY_FULL]:
			self.symmetry[symType] = float(configDict.get(SYMMETRY, {}).get(symType, 0))
			symmetrySum += self.symmetry[symType]
		if (symmetrySum > 0):
			# normalize probabilities
			for symType in self.symmetry.keys():
				self.symmetry[symType] /= symmetrySum
		else:
			# no valid symmetry types; use default
			self.symmetry = {DEFAULTS[SYMMETRY]: 1}

		self.accel = {}
		accelConfig = [float(x) for x in configDict.get(ACCEL, "").split() if x]
		for key in [ACCEL_MIN, ACCEL_MAX, ACCEL_FWD, ACCEL_LAT]:
			if (accelConfig):
				self.accel[key] = accelConfig.pop(0)
			else:
				self.accel[key] = DEFAULTS[ACCEL][key]
		if (self.accel[ACCEL_MIN] < 0):
			self.accel[ACCEL_MIN] = 0
		if (self.accel[ACCEL_MAX] < self.accel[ACCEL_MIN]):
			self.accel[ACCEL_MAX] = self.accel[ACCEL_MIN]
		if (self.accel[ACCEL_FWD] > 1):
			self.accel[ACCEL_FWD] = 1
		if (self.accel[ACCEL_LAT] > self.accel[ACCEL_FWD]):
			self.accel[ACCEL_LAT] = self.accel[ACCEL_FWD]

		self.turn = {}
		turnConfig = [float(x) for x in configDict.get(TURN, "").split() if x]
		for key in [TURN_MIN, TURN_MAX]:
			if (turnConfig):
				self.turn[key] = turnConfig.pop(0)
			else:
				self.turn[key] = DEFAULTS[TURN][key]
		if (self.turn[TURN_MIN] < 0):
			self.turn[TURN_MIN] = 0
		if (self.turn[TURN_MAX] < self.turn[TURN_MIN]):
			self.turn[TURN_MAX] = self.turn[TURN_MIN]

		powerSum = 0
		self.power = {}
		for powerType in [POWER_MIN, POWER_STD, POWER_HIGH, POWER_MAX]:
			self.power[powerType] = float(configDict.get(POWER, {}).get(powerType, 0))
			powerSum += self.power[powerType]
		if (powerSum > 0):
			# normalize probabilities
			for powerType in self.power.keys():
				self.power[powerType] /= powerSum
		else:
			# no valid power types; use default
			self.power = {DEFAULTS[POWER]: 1}

		self.parts = {}
		for part in configDict.get(PARTS, {}).keys():
			if (part not in Parts.parts[self.size]):
#####
##
				#warn about unrecognized part
##
#####
				continue
			partConfig = configDict[PARTS][part]
			if (not partConfig):
				continue
			partDict = {}
			if (partConfig[0] == '"'):
				idx = partConfig.find('"', 1)
				if (idx > 0):
					partDict[PART_DISTRIBUTION] = partConfig[1 : idx]
					partConfig = partConfig[idx + 1:]
			partConfig = [x for x in partConfig.split() if x]
			if (PART_DISTRIBUTION not in partDict):
				partDict[PART_DISTRIBUTION] = partConfig.pop(0)
			if (partDict[PART_DISTRIBUTION] not in Dists.dists):
#####
##
				#warn about unrecognized distribution
##
#####
				continue
			self.parts[part] = partDict
			for key in [PART_MIN, PART_MAX]:
				if (partConfig):
					x = int(partConfig.pop(0))
					if (x >= 0):
						self.parts[part][key] = x

		self.rooms = {}
		for room in configDict.get(ROOMS, {}).keys():
			if (room not in Rooms.rooms):
#####
##
				#warn about unrecognized room
##
#####
				continue
			roomConfig = configDict[ROOMS][room]
			if (not roomConfig):
				continue
			roomDict = {}
			if (roomConfig[0] == '"'):
				idx = roomConfig.find('"', 1)
				if (idx > 0):
					roomDict[ROOM_DISTRIBUTION] = roomConfig[1 : idx]
					roomConfig = roomConfig[idx + 1:].strip()
			roomConfig = [x for x in roomConfig.split() if x]
			if (ROOM_DISTRIBUTION not in roomDict):
				roomDict[ROOM_DISTRIBUTION] = roomConfig.pop(0)
			if (roomDict[ROOM_DISTRIBUTION] not in Dists.dists):
#####
##
				#warn about unrecognized distribution
##
#####
				continue
			self.rooms[room] = roomDict
			for key in [ROOM_MIN, ROOM_MAX]:
				if (roomConfig):
					x = int(roomConfig.pop(0))
					if (x >= 0):
						self.rooms[room][key] = x

	def fixCounts(self, partCounts, roomCounts):
		# first pass: each room individually
		partMins = {}
		for room in roomCounts.keys():
			for (part, partDict) in Rooms.rooms[room].parts.items():
				if ((roomCounts[room] * partDict[PART_MIN]) > partCounts.get(part, 0)):
					# reduce room count (to minimum of self.rooms[room][ROOM_MIN])
					roomCounts[room] = max(int(partCounts.get(part, 0) / partDict[PART_MIN]), self.rooms[room][ROOM_MIN])
				if ((roomCounts[room] * partDict[PART_MIN]) > partCounts.get(part, 0)):
					# increase part count (to maximum of self.parts[part][PART_MAX])
					partCounts[part] = min(roomCounts[room] * partDict[PART_MIN], self.parts[part][PART_MAX])
				if ((roomCounts[room] * partDict[PART_MIN]) > partCounts.get(part, 0)):
					# insufficient parts to meet room requirements; remove room
					roomCounts[room] = 0
					break
				partMins[part] = partMins.get(part, 0) + (roomCounts[room] * partDict[PART_MIN])

		# second pass: all rooms together
		for part in partMins.keys():
			tryReduce = True
			while ((partMins[part] > partCounts.get(part, 0)) and (tryReduce)):
				# reduce count of all affected rooms with count > self.rooms[room][ROOM_MIN]
				tryReduce = False
				for room in roomCounts.keys():
					if ((Rooms.rooms[room].parts.get(part, 0) > 0) and (roomCounts[room] > self.rooms[room][ROOM_MIN])):
						tryReduce = True
						roomCounts[room] -= 1
						for (roomPart, roomPartDict) in Rooms.rooms[room].parts.items():
							partMins[roomPart] -= roomPartDict[PART_MIN]
			if (partMins[part] > partCounts.get(part, 0)):
				# increase part count (to maximum of self.parts[part][PART_MAX])
				partCounts[part] = min(roomCounts[room] * partDict[PART_MIN], self.parts[part][PART_MAX])
			if (partMins[part] > partCounts.get(part, 0)):
				# insufficient parts to meet room requirements; remove highest-count room until requirements met
				affectedRooms = [(room, roomCounts[room] * Rooms.rooms[room].parts.get(part, 0)) for room in roomCounts.keys()]
				affectedRooms.sort(key=lambda t: t[1])
				while (partMins[part] > partCounts.get(part, 0)):
					(room, partCount) = affectedRooms.pop(0)
					for (roomPart, roomPartDict) in Rooms.rooms[room].parts.items():
						partMins[roomPart] -= roomPartDict[PART_MIN] * roomCounts[room]
					roomCounts[room] = 0

	def generateShip(self):
		material = Util.randomDict(self.materials)
		enclosure = Util.randomDict(self.enclosure)
		symmetry = Util.randomDict(self.symmetry)
		accel = random.uniform(self.accel[ACCEL_MIN], self.accel[ACCEL_MAX])
		if (not Parts.thrusters[self.size]):
#####
##
			# warn about no thrusters of appropriate size
##
#####
			accel = 0
		accelFactorFwd = random.uniform(self.accel[ACCEL_FWD], 1)
		accelFactorLat = random.uniform(self.accel[ACCEL_LAT], accelFactorFwd)
		turn = random.uniform(self.turn[TURN_MIN], self.turn[TURN_MAX])
		if (not Parts.gyros[self.size]):
#####
##
			# warn about no gyros of appropriate size
##
#####
			turn = 0
		power = Util.randomDict(self.power)
		if (not Parts.reactors[self.size]):
#####
##
			# warn about no reactors of appropriate size
##
#####
			power = None
		# select parts and rooms
		partCounts = {}
		for part in self.parts.keys():
			n = Dists.dists[self.parts[part][PART_DISTRIBUTION]].getCount()
			if ((PART_MIN in self.parts[part]) and (n < self.parts[part][PART_MIN])):
				n = self.parts[part][PART_MIN]
			if ((PART_MAX in self.parts[part]) and (n > self.parts[part][PART_MAX])):
				n = self.parts[part][PART_MAX]
			if (n > 0):
				partCounts[part] = n
		roomCounts = {}
		for room in self.rooms.keys():
			n = Dists.dists[self.rooms[room][ROOM_DISTRIBUTION]].getCount()
			if ((ROOM_MIN in self.rooms[room]) and (n < self.rooms[room][ROOM_MIN])):
				n = self.rooms[room][ROOM_MIN]
			if ((ROOM_MAX in self.rooms[room]) and (n > self.rooms[room][ROOM_MAX])):
				n = self.rooms[room][ROOM_MAX]
			if (n > 0):
				roomCounts[room] = n
		self.fixCounts(partCounts, roomCounts)
		roomCounts[Rooms.EXTERIOR] = 1
		partsMass = 0
		partsPower = 0
		maxPartPower = 0
		for part in partCounts.keys():
			if (part not in Parts.parts[self.size]):
				continue
			partsMass += Parts.parts[self.size][part].mass * partCounts[part]
			partsPower += Parts.parts[self.size][part].power * partCounts[part]
			if (Parts.parts[self.size][part].power > maxPartPower):
			    maxPartPower = Parts.parts[self.size][part].power
		# assign parts to rooms
		rooms = {}
		for room in roomCounts.keys():
			if (roomCounts[room] <= 0):
				continue
			rooms[room] = []
			for i in xrange(roomCounts[room]):
				roomDict = {}
				for (part, partDict) in Rooms.rooms[room].parts.items():
					roomDict[part] = partDict[PART_MIN]
					partCounts[part] -= roomDict[part]
				rooms[room].append(roomDict)
		for part in partCounts.keys():
			if (partCounts[part] <= 0):
				continue
			probSum = 0
			probDict = {}
			for (room, prob) in Parts.parts[self.size][part].rooms.items():
				if ((prob > 0) and (rooms.has_key(room))):
					probDict[room] = prob
					probSum += prob
			if (probSum > 0):
				# normalize probabilities
				for room in probDict.keys():
					probDict[room] /= probSum
			while ((probDict) and (partCounts[part] > 0)):
				room = Util.randomDict(probDict)
				maxCount = Rooms.rooms[room].parts.get(part, {}).get(PART_MAX)
				roomList = [r for r in rooms[room] if (maxCount is None) or (r.get(part, 0) < maxCount)]
				if (not roomList):
					# remove room from probDict, renormalizing first
					probSum = 1 - probDict[room]
					if (probSum <= 0):
						break
					for r in probDict.keys():
						probDict[r] /= probSum
					del probDict[room]
					continue
				roomDict = random.choice(roomList)
				roomDict[part] = roomDict.get(part, 0) + 1
				partCounts[part] -= 1
		# dump remaining unassigned parts into "general parts" pseudo-room
		generalParts = {}
		for part in partCounts.keys():
			if (partCounts[part] > 0):
				generalParts[part] = partCounts[part]
		# generate layout and add thrusters, gyros, and reactors
		thrusters = {}
		thrustersMass = {}
		thrustersThrust = {}
		thrustersPower = {}
		gyros = {}
		gyrosMass = 0
		gyrosTurn = 0
		gyrosPower = 0
		reactors = {}
		reactorsMass = 0
		reactorsPower = 0
		needsWork = True
		while (needsWork):
#####
##
#need logic in this loop to ensure we don't go crazy; give up on fully meeting thrust/turn requirements after a few passes
##
#####
			needsWork = False
			# generate layout
#####
##
			#generate layout
			# determine mass
			mass = partsMass + sum(m for m in thrustersMass.values()) + gyrosMass + reactorsMass #+ $structure_mass
##
#####
			# add thrusters if necessary
			thrustReq = {ACCEL: mass * accel}
			thrustReq[ACCEL_FWD] = thrustReq[ACCEL] * accelFactorFwd
			thrustReq[ACCEL_LAT] = thrustReq[ACCEL] * accelFactorLat
			for d in thrustReq.keys():
				if (thrustersThrust.get(d, 0) < thrustReq[d]):
					needsWork = True
					# remove existing thrusters to realize efficiency gains from larger thrusters
					thrusters[d] = {}
					thrustersMass[d] = 0
					thrustersThrust[d] = 0
					thrustersPower[d] = 0
					# add necessary thrusters
					while (thrustReq[d] > 0):
						for thruster in Parts.thrusters.get(self.size, []):
							if (thruster.thrust > thrustReq[d]):
								break
						n = max(int(math.ceil(thrustReq[d] / thruster.thrust)), 1)
						thrusters[d][thruster] = thrusters[d].get(thruster, 0) + n
						thrustersMass[d] += n * thruster.mass * THRUST_DIRECTION_COUNTS[d]
						thrustersThrust[d] += n * thruster.thrust
						thrustersPower[d] += n * thruster.power * THRUST_DIRECTION_COUNTS[d]
						thrustReq[d] -= n * thruster.thrust
			# add gyros if necessary
			turnReq = mass * turn
			if (gyrosTurn < turnReq):
				needsWork = True
				# remove existing gyros to realize efficiency gains from larger gyros
				gyros = {}
				gyrosMass = 0
				gyrosTurn = 0
				gyrosPower = 0
				# add necessary gyros
				while (turnReq > 0):
					for gyro in Parts.gyros.get(self.size, []):
						if (gyro.turn > turnReq):
							break
					n = max(int(math.ceil(turnReq / gyro.turn)), 1)
					gyros[gyro] = gyros.get(gyro, 0) + n
					gyrosMass += n * gyro.mass
					gyrosTurn += n * gyro.turn
					gyrosPower += n * gyro.power
					turnReq -= n * gyro.turn
			# add reactors if necessary
			if (power == POWER_MIN):
				# largest of: 150% of aft-facing thrusters, all gyros, largest single part
				powerReq = max(1.5 * thrustersPower[ACCEL], gyrosPower, maxPartPower)
			elif (power == POWER_STD):
				# largest of: 150% of aft and single lateral thrusters, 150% of aft thrusters and all gyros, all parts
				powerReq = max(1.5 * (thrustersPower[ACCEL] + thrustersPower[ACCEL_LAT]),
						1.5 * thrustersPower[ACCEL] + gyrosPower, partsPower)
			elif (power == POWER_HIGH):
				# largest of: 150% of aft and two lateral thrusters, 150% of aft and single lateral thrusters and all gyros,
				# 100% of aft-facing thrusters plus all gyros and all parts
				powerReq = max(1.5 * (thrustersPower[ACCEL] + 2 * thrustersPower[ACCEL_LAT]),
						1.5 * (thrustersPower[ACCEL] + thrustersPower[ACCEL_LAT]) + gyrosPower,
						thrustersPower[ACCEL] + gyrosPower + partsPower)
			elif (power == POWER_MAX):
				# 150% of aft and two lateral thrusters plus all gyros and all parts
				powerReq = 1.5 * (thrustersPower[ACCEL] + 2 * thrustersPower[ACCEL_LAT]) + gyrosPower + partsPower
			else:
				# no power requirements, so zero
				powerReq = 0
			if (reactorsPower < powerReq):
				needsWork = True
				# remove existing reactors to realize efficiency gains from larger reactors
				reactors = {}
				reactorsMass = 0
				reactorsPower = 0
				# add necessary reactors
				while (powerReq > 0):
					# note reversal of signs below, as reactor.power is negative
					for reactor in Parts.reactors.get(self.size, []):
						if (-reactor.power > powerReq):
							break
					n = max(int(math.ceil(powerReq / -reactor.power)), 1)
					reactors[reactor] = reactors.get(reactor, 0) + n
					reactorsMass += n * reactor.mass
					reactorsPower -= n * reactor.power
					powerReq += n * reactor.power
#####
##
		#...
		print "material: %s"%material
		print "enclosure: %s"%enclosure
		print "symmetry: %s"%symmetry
		print "accel: %s (%s, %s)"%(accel,accelFactorFwd,accelFactorLat)
		print "turn: %s"%turn
		print "power: %s"%power
		print "parts mass: %s"%partsMass
		print "part assignments: %s"%rooms
		print "unassigned parts: %s"%generalParts
		print "thrusters: %s"%thrusters
		print "accel: %s (%s, %s)"%(thrustersThrust[ACCEL]/mass,thrustersThrust[ACCEL_FWD]/mass,thrustersThrust[ACCEL_LAT]/mass)
		print "gyros: %s (turn: %s)"%(gyros,gyrosTurn/mass)
		print "reactors: %s (power: %s)"%(reactors,reactorsPower)
		print "mass: %s"%mass
##
#####


def init():
	global initialized
	if (initialized):
		return
	Dists.init()
	Parts.init()
	Rooms.init()
	for (shipType, typeAbbr) in TYPE_ABBRS.items():
		classes[shipType] = {}
		configPath = os.path.join(shipgenDir, "data", "classes_%s.cfg" % typeAbbr)
		configDict = ConfigFile.readFile(configPath)
		for className in configDict.keys():
			if (type(configDict[className]) != type({})):
				continue
			classes[shipType][className] = ShipClass(shipType, configDict[className])
	initialized = True