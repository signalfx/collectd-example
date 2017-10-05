#!/usr/bin/python

# Sample python plugin
# For more information see https://collectd.org/documentation/manpages/collectd-python.5.shtml
import logging
import sys
import sfx_collectd_utilities as sfx
import time
# from math import pi, sin

try:
    import collectd

except ImportError:
    try:
        import dummy_collectd as collectd
    except:
        pass

# set the plugin name as a global variable
PLUGIN_NAME = 'hello-world'

# this instantiates sfx_utilities.CollectdLogger
log = logging.getLogger(PLUGIN_NAME)

# keep a global count of the number of instances configured
INSTANCE_COUNT = 0


def config(conf):
    """
    This method has been registered as the config callback and is used to parse options from
    given config.  Note that you cannot receive the whole config files this way, only Module blocks
    inside the Python configuration block. Additionally you will only receive blocks where your
    callback identifier matches your plugin.

    In this case Frequency is a float value that will modify the frequency of the sine wave. This
    in conjunction with the polling interval can give you as smooth or blocky a curve as you want.

    :param conf: a Config object
    :return: None
    """
    # configurations should be parsed and stored in this data object
    # some defaults are initialized
    data = {
        'InstanceID': "{0}-{1}".format(PLUGIN_NAME, INSTANCE_COUNT),
        'LogLevel': logging.INFO,
        'Dimensions': {}
    }

    # create the logger for the new plugin instance with default level of INFO
    log = logging.getLogger(data['InstanceID'])

    for kv in conf.children:
        # log the configuration keys
        log.debug(str(kv))
        # users should be able to set the log level for each module block
        # if LogLevel is the first configuration in the module block, it will be parsed first
        if kv.key == 'LogLevel':
            data['LogLevel'] = sfx.get_log_level_from_config(kv.values[0])
            log.setLevel(data['LogLevel'])
        # users should be able to specify an interval for each module block
        elif kv.key == 'Interval':
            data[kv.key] = float(kv.values[0])
        # plugins should parse user specified dimensions that will be appended to all emitted metrics
        elif kv.key == 'Dimension':
            if len(kv.values) >= 2:
                key = str(kv.values[0])
                val = str(kv.values[1])
                if sfx.isValidDimensionKey(key):
                    data['Dimensions'][key] = val
                else:
                    log.warning("Unable to parse dimension {}".format(kv.values))
            else:
                log.warning("Unable to parse dimension {}".format(kv.values))
        # additional configuration keys can be specified and parsed accordingly
        elif kv.key == 'ConfigKey1':
            log.info(kv.values[0])
            data[kv.key] = kv.values[0]

    # Register a read callback with the data dictionary.  When collectd invokes
    # the read callback it will pass back the data dictionary.
    if 'Interval' in data:  # register with user specified interval
        collectd.register_read(read, data['Interval'], data=data, name=data['InstanceID'])
    else:  # register with out an interval to use collectd default
        collectd.register_read(read, data=data, name=data['InstanceID'])

    # Increment the instance count once a read call back is registered for the instance
    global INSTANCE_COUNT
    INSTANCE_COUNT = INSTANCE_COUNT + 1


def read(data):
    """
    This method has been registered as the read callback and will be called every polling interval
    to dispatch metrics.  We emit three metrics: one gauge, a sine wave; two counters for the
    number of datapoints and notifications we've seen.

    :return: None
    """
    # val = sin(time.time() * 2 * pi / 60 * FREQUENCY)
    # collectd.Values(plugin=PLUGIN_NAME,
    #                 type_instance="sine",
    #                 plugin_instance=PLUGIN_INSTANCE % FREQUENCY,
    #                 type="gauge",
    #                 values=[val]).dispatch()

    # collectd.Values(plugin=PLUGIN_NAME,
    #                 type_instance="datapoints",
    #                 type="counter",
    #                 values=[DATAPOINT_COUNT]).dispatch()

    # collectd.Values(plugin=PLUGIN_NAME,
    #                 type_instance="notifications",
    #                 type="counter",
    #                 values=[NOTIFICATION_COUNT]).dispatch()

    # get the logger for the instance which should be set to the appropriate logging level
    global log
    log = logging.getLogger(data['InstanceID'])

    # log the data object as debug information
    log.debug(data)

    log.info("READING CALLBACK")
    # log.info(str(data))


def init():
    """
    This method has been registered as the init callback; this gives the plugin a way to do startup
    actions.  We'll just log a message.

    :return: None
    """

    log.info("Plugin %s initializing..." % PLUGIN_NAME)


def shutdown():
    """
    This method has been registered as the shutdown callback. this gives the plugin a way to clean
    up after itself before shutting down.  We'll just log a message.

    :return: None
    """
    log.info("Plugin %s shutting down..." % PLUGIN_NAME)


# def write(values):
#     """
#     This method has been registered as the write callback. Let's count the number of datapoints
#     and emit that as a metric.

#     :param values: Values object for datapoint
#     :return: None
#     """

#     global DATAPOINT_COUNT
#     DATAPOINT_COUNT += len(values.values)


# def flush(timeout, identifier):
#     """
#     This method has been registered as the flush callback.  Log the two params it is given.

#     :param timeout: indicates that only data older than timeout seconds is to be flushed
#     :param identifier: specifies which values are to be flushed
#     :return: None
#     """
#     log.info("Plugin {} flushing timeout {} and identifier {}".format(PLUGIN_NAME,
#                                                                       timeout,
#                                                                       identifier))


# def notification(notif):
#     """
#     This method has been regstered as the notification callback. Let's count the notifications
#     we receive and emit that as a metric.

#     :param notif: a Notification object.
#     :return: None
#     """

#     global NOTIFICATION_COUNT
#     NOTIFICATION_COUNT += 1


if __name__ != "__main__":
    # when running inside plugin register each callback
    collectd.register_config(config)
    collectd.register_init(init)
    collectd.register_shutdown(shutdown)

    # the following registrations are used for intercepting
    # data points and notifications emitted through collectd
    # collectd.register_write(write)
    # collectd.register_flush(flush)
    # collectd.register_notification(notification)
else:
    # outside plugin just collect the info
    read()
    if len(sys.argv) < 2:
        while True:
            time.sleep(10)
            read()
