#!/usr/bin/env python
import XenAPI
import time
import pickle
import struct
import socket
import json

class XenStats:
    def __init__(self, config):
        self.prefix = config["prefix"]
        self.graphite_addr = tuple(config["graphite_addr"])
        self.session = XenAPI.Session(config["url"])
        self.session.xenapi.login_with_password(config["username"], config["password"])
        
    def read_data_sources(self, vm):
        ret = {}
        data_sources = self.session.xenapi.VM.get_data_sources(vm)
        for ds in data_sources:
            name = ds["name_label"]
            if not ds["enabled"]: continue
            if  not name.startswith("cpu") and \
                not name.startswith("vif") and \
                not name.startswith("vbd") and \
                not name == "memory" and \
                not name == "memory_internal_free":
                continue
            
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
            ret[vmr["name_label"]] = self.read_data_sources(vm)
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

if __name__ == '__main__':
    XenStats(json.load(open('config.json'))).send_to_graphite()
    