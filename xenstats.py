#!/usr/bin/env python
import os
import XenAPI
import time
import pickle
import struct
import socket
import json

ROOT = os.path.abspath(os.path.dirname(__file__))

class XenStats:
	def __init__(self, config):
		self.prefix = config["prefix"]
		self.graphite_addr = tuple(config["address"])
		self.session = XenAPI.Session(config["url"])
		self.session.xenapi.login_with_password(config["username"], config["password"])
		
	def read_data_sources(self, vm):
		ret = {}
		data_sources = self.session.xenapi.VM.get_data_sources(vm)
		for ds in data_sources:
			if not ds["enabled"]: continue

			try:
				ret[ds["name_label"]] = (int(time.time()), self.session.xenapi.VM.query_data_source(vm, ds["name_label"]))
			except:
				pass
		
		return ret

	def fetch_all(self):
		ret = {}
		for vm in self.session.xenapi.VM.get_all():
			vmr = self.session.xenapi.VM.get_record(vm)
			if vmr["power_state"] != "Running": continue
			if vmr["is_control_domain"]: continue
			ret[vmr["uuid"]] = self.read_data_sources(vm)
		return ret
	
	def __send(self, metrics):
		payload = pickle.dumps(metrics)
		header = struct.pack("!L", len(payload))
		
		graphite = socket.socket()
		graphite.connect(self.graphite_addr)
		graphite.sendall(header + payload)
		graphite.close()
	
	def send_to_graphite(self):
		vms = self.fetch_all()
		for vm in vms: 
			metrics = []
			for metric in vms[vm]:
				metrics += [(
					self.prefix + vm + '.' + metric,
					vms[vm][metric]
				)]
			self.__send(metrics)

def main():
	config = json.load(open(ROOT + '/config.json'))
	for cluster in config["clusters"]:
		c = dict(config["clusters"][cluster].items() + config["graphite"].items())
		XenStats(c).send_to_graphite()
	return
	XenStats().send_to_graphite()

if __name__ == '__main__':
	main()