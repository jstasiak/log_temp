#!/usr/bin/python
#-*- coding: utf-8 -*-

import os
import json
import rrdtool
import sys

from errno import EEXIST
from itertools import product
from math import ceil
from os import makedirs, remove
from os.path import abspath, dirname, expanduser, isdir, isfile, join
from time import sleep

PROJECT_ROOT = abspath(dirname(__file__))

def read_config():
	data = {}
	for name in ('default_config.json', 'config.json'):
		full_name = join(PROJECT_ROOT, name)
		try:
			with open(full_name) as fd:
				data.update(json.load(fd))
		except IOError:
			pass

	assert data
	return data

def write_config(data):
	with open(join(PROJECT_ROOT, 'config.json'), 'w') as fd:
		json.dump(data, fd, sort_keys = True, indent = 4, separators = (',', ': '))

def expand_path(path):
	path = expanduser(path)
	if not path.startswith('/'):
		path = join(PROJECT_ROOT, path)

	return path

def mkdirp(path):
	try:
		makedirs(path)
	except OSError as e:
		if e.errno == EEXIST and isdir(path):
			pass
		else:
			raise

def sensor_graph_file(sensor, start):
	config = read_config()
	return join(expand_path(config['graphs_path']), '{0}-{1}.png'.format(sensor,
		start.replace('-', '')))

def do_graph(graph, sensor, database, start):
	result = rrdtool.graph(str(graph),
			'--imgformat', 'PNG',
			'--font', 'DEFAULT:0:/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf',
			'--color', 'BACK#FFFFFFFF',
			'--color', 'CANVAS#FFFFFF00',
			'--border', '0', 
			'--width', '775',
			'--height', '279',
			'--slope-mode',
			'--start', str(start),
			'--vertical-label', 'Temperature °C',
			'--title', str(sensor),
			'--lower-limit', '0',
			'DEF:T=%s:t:AVERAGE' % str(database),
			'LINE1:T#FF3300:Temperature  \t',
			'GPRINT:T:MAX:Max\: %6.2lf°C\t',
			'GPRINT:T:MIN:Min\: %6.2lf°C\t',
			'GPRINT:T:AVERAGE:Average\: %6.2lf°C\t',
			'GPRINT:T:LAST:Current\: %6.2lf°C\c',
	)

def generate_rrdtool_create_parameters():
	SECONDS_IN_MINUTE = 60
	SECONDS_IN_HOUR = 3600
	HOURS_IN_DAY = 24
	SECONDS_IN_DAY = SECONDS_IN_HOUR * HOURS_IN_DAY
	rra_in = (
		(SECONDS_IN_MINUTE, SECONDS_IN_HOUR),
		(SECONDS_IN_MINUTE, SECONDS_IN_DAY),
		(SECONDS_IN_HOUR, SECONDS_IN_DAY * 7),
		(SECONDS_IN_HOUR * 3, SECONDS_IN_DAY * 100),
	)
	rra = []

	unit_seconds = 60
	parameters = [
		'-s %d' % (unit_seconds,),
		'DS:t:GAUGE:600:U:U',
	]

	for (slot_seconds, keep_slot_for_seconds), type in product(rra_in, ('AVERAGE', 'MIN', 'MAX')):
		slot_units = int(ceil(slot_seconds * 1.0 / unit_seconds))
		keep_slot_for_units = int(ceil(keep_slot_for_seconds * 1.0 / unit_seconds))
		parameters.append('RRA:%s:0.5:%d:%d' % (type, slot_units, keep_slot_for_units,))

	return parameters


def main():
	handle_temperatures(get_temperatures())

def handle_temperatures(temperatures):
	for sensor, temperature in temperatures.items():
		handle_sensor_value(sensor, temperature)

def handle_sensor_value(sensor, value):
	config = read_config()
	config['sensor_names'].setdefault(sensor, sensor)
	write_config(config)

	name = config['sensor_names'][sensor]
	print "sensor %s (%s) - %s C" % (config['sensor_names'][sensor], sensor, value)

	save_sensor_value(sensor, value)
	generate_graphs_for_sensor(sensor)

def save_sensor_value(sensor, value):
	database = rrd_path(sensor)
	mkdirp(dirname(database))
	if not isfile(database):
		params = generate_rrdtool_create_parameters()
		rrdtool.create(str(database), *params)

	rrdtool.update(str(database), 'N:%s' % (value,))

def rrd_path(sensor):
	config = read_config()
	return join(expand_path(config['databases_path']), "%s.rrd" % sensor)

def generate_graphs_for_sensor(sensor):
	config = read_config()
	name = config['sensor_names'][sensor]
	database = rrd_path(sensor)
	for start in config['graphs']:
		path = sensor_graph_file(name, start)
		mkdirp(dirname(path))
		do_graph(sensor_graph_file(name, start), sensor, database, start)


def get_temperatures():
	config = read_config()
	digitemp_config = join(PROJECT_ROOT, 'digitemp.conf')
	output = os.popen("digitemp_DS9097 -c {conf} -s {port} -a -q -o '%R %.2C' -i".format(
		conf = digitemp_config, port = config['port'])).readlines()
	remove(digitemp_config)

	lines = [line.split() for line in output]
	lines = [line for line in lines if len(line) == 2]
	temperatures = dict((sensor, float(temperature)) for (sensor, temperature) in lines)
	return temperatures

if __name__ == '__main__':
	period = int(sys.argv[1]) if len(sys.argv) > 1 else 0

	main()
	while period:
		sleep(period)
		main()
