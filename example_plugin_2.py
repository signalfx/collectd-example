#!/usr/bin/python

# Sample python plugin
# For more information see https://collectd.org/documentation/manpages/collectd-python.5.shtml
import logging
import sys
import sfx_utilities as sfx
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
INSTANCE_COUNT = 0
DEFAULT_INTERVAL = 10.0
DATAPOINT_COUNT = 0
NOTIFICATION_COUNT = 0
PLUGIN_INSTANCE = "example[frequency=%s]"
SEND = True


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
        'Interval': DEFAULT_INTERVAL,
        'LogLevel': logging.INFO,
        'Dimensions': {}
    }

    # create the logger for the new plugin instance with default level of INFO
    log = logging.getLogger(data['InstanceID'])

    for kv in conf.children:
        # debug configuration keys
        log.debug(str(kv))
        if kv.key == 'LogLevel':
            level = sfx.getLogLevelFromConfig(kv.values[0])
            log.setLevel(level)
            data['LogLevel'] = level
        elif kv.key == 'Interval':
            data[kv.key] = float(kv.values[0])
        elif kv.key == 'Dimension':
            if len(kv.values) >= 2:
                # TODO: validate the key with ingest's validation
                key = kv.values[0]
                val = kv.values[1]
                data['Dimensions'][str(key)] = str(val)
            else:
                log.warning("Unable to parse dimension {}".format(kv.values))
        elif kv.key == 'ConfigKey1':
            collectd.info(kv.values[0])
            data[kv.key] = kv.values[0]

    collectd.info(str(sfx.str_to_bool("false")))
    log.info("THIS IS A TEST OF THE LOG CLASS")
    log.debug("THIS SHOULDN'T APPEAR")
    log.setLevel(logging.DEBUG)
    log.debug("THIS SHOULD SHOW UP")

    # Register a read callback with the data dictionary.  When collectd invokes
    # the read callback it will pass back the dictionary.
    collectd.register_read(
                            read,
                            data['Interval'],
                            data=data,
                            name=data['InstanceID']
    )

    # Increment the instance count
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

    # Set verbosity for this instance
    global log
    log = logging.getLogger(data['InstanceID'])

    log.info("READING CALLBACK")
    log.info(str(data))

    global SEND
    if SEND:
        notif = collectd.Notification(plugin=PLUGIN_NAME,
                                      type_instance="started",
                                      type="objects")  # need a valid type for notification
        notif.severity = 4  # OKAY
        notif.message = "The %s plugin has just started" % PLUGIN_NAME
        notif.dispatch()
        SEND = False


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

    # always invoke the sfx.shutdown function to clean up log handlers
    # sfx.shutdown(PLUGIN_NAME)


def write(values):
    """
    This method has been registered as the write callback. Let's count the number of datapoints
    and emit that as a metric.

    :param values: Values object for datapoint
    :return: None
    """

    global DATAPOINT_COUNT
    DATAPOINT_COUNT += len(values.values)


def flush(timeout, identifier):
    """
    This method has been registered as the flush callback.  Log the two params it is given.

    :param timeout: indicates that only data older than timeout seconds is to be flushed
    :param identifier: specifies which values are to be flushed
    :return: None
    """
    log.info("Plugin {} flushing timeout {} and identifier {}".format(PLUGIN_NAME,
                                                                      timeout,
                                                                      identifier))


def notification(notif):
    """
    This method has been regstered as the notification callback. Let's count the notifications
    we receive and emit that as a metric.

    :param notif: a Notification object.
    :return: None
    """

    global NOTIFICATION_COUNT
    NOTIFICATION_COUNT += 1


if __name__ != "__main__":
    # when running inside plugin register each callback
    collectd.register_config(config)
    collectd.register_init(init)
    collectd.register_shutdown(shutdown)
    collectd.register_write(write)
    collectd.register_flush(flush)
    collectd.register_notification(notification)
else:
    # outside plugin just collect the info
    read()
    if len(sys.argv) < 2:
        while True:
            time.sleep(10)
            read()
