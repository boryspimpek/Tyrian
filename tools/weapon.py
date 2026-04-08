#!/bin/env python

import json
import sys
import struct
import os

WEAP_NUM = 780

struct_fmt = "<H BBHBBBB 8B8B8b8b8b8b8H bbBBBB"

def unpack_weapon(str):
	tup = struct.unpack(struct_fmt, str)
	dict = {}

	dict['drain'] = tup[0]
	dict['shotRepeat'] = tup[1]
	dict['multi'] = tup[2]
	dict['weapAni'] = tup[3]
	dict['max'] = tup[4]
	dict['tx'] = tup[5]
	dict['ty'] = tup[6]
	dict['aim'] = tup[7]

	i = 8

	tmp = [{} for j in range(8)]
	for j in range(8):
		tmp[j]['attack'] = tup[i]
		i += 1
	for j in range(8):
		tmp[j]['del'] = tup[i]
		i += 1
	for j in range(8):
		tmp[j]['sx'] = tup[i]
		i += 1
	for j in range(8):
		tmp[j]['sy'] = tup[i]
		i += 1
	for j in range(8):
		tmp[j]['bx'] = tup[i]
		i += 1
	for j in range(8):
		tmp[j]['by'] = tup[i]
		i += 1
	for j in range(8):
		tmp[j]['sg'] = tup[i]
		i += 1
	dict['patterns'] = tmp

	dict['acceleration'] = tup[i]
	dict['accelerationx'] = tup[i+1]
	dict['circleSize'] = tup[i+2]
	dict['sound'] = tup[i+3]
	dict['trail'] = tup[i+4]
	dict['shipBlastFilter'] = tup[i+5]
	
	return dict

def weapon_to_dict(weapon_data, index=None):
	"""Convert weapon data to dict format for JSON serialization."""
	if index is not None:
		weapon_data['index'] = "%04X" % index
	return weapon_data


def toJSON(hdt, output):
	try:
		f = open(hdt, "rb")
	except IOError:
		print("%s couldn't be opened for reading." % (hdt,))
		sys.exit(1)

	try:
		outf = open(output, "w")
	except IOError:
		print("%s couldn't be opened for writing." % (output,))
		sys.exit(1)

	f.seek(struct.unpack("<i", f.read(4))[0])
	f.read(7*2)


	sys.stdout.write("Converting weapons")
	index = 0

	weapons = []
	for i in range(WEAP_NUM+1):
		tmp = f.read(struct.calcsize(struct_fmt))
		shot = unpack_weapon(tmp)
		weapons.append(weapon_to_dict(shot, index))
		index += 1

		sys.stdout.write(".")
		sys.stdout.flush()

	sys.stdout.write("Done!\n")
	sys.stdout.write("Writing JSON...")
	sys.stdout.flush()
	json.dump({"TyrianHDT": {"weapon": weapons}}, outf, indent="\t")
	sys.stdout.write("Done!\n")

if __name__ == "__main__":
	script_dir = os.path.dirname(os.path.abspath(__file__))
	default_hdt = os.path.join(script_dir, "tyrian.hdt")
	default_json = os.path.join(script_dir, "weapon.json")

	if len(sys.argv) == 1:
		# No args - use defaults
		hdt_path = default_hdt
		json_path = default_json
	elif len(sys.argv) == 3:
		# Custom paths: weapon.py input.hdt output.json
		hdt_path = sys.argv[1]
		json_path = sys.argv[2]
	else:
		print("Usage: weapon.py [input.hdt] [output.json]")
		print("Default: weapon.py (uses tyrian.hdt -> tyrian.json in script dir)")
		sys.exit(1)

	toJSON(hdt_path, json_path)
