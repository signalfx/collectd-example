#!/usr/bin/python

import collectd
import threading

PLUGIN_NAME = 'dpmcounter'
DATAPOINT_COUNT = {}
METRIC_LOCK = threading.Lock()

def read():
    with METRIC_LOCK:
        for k,v in DATAPOINT_COUNT.items():
            collectd.Values(plugin=PLUGIN_NAME, type_instance="dpm", plugin_instance=k, type="counter", values=[v]).dispatch()

def write(values_obj):
    global DATAPOINT_COUNT
    with METRIC_LOCK:
        per_plugin = DATAPOINT_COUNT.setdefault(values_obj.plugin, 0)
        DATAPOINT_COUNT[values_obj.plugin] = per_plugin + len(values_obj.values)

collectd.register_read(read)
collectd.register_write(write)
