#!/usr/bin/python

# Sample python plugin
# For more information see https://collectd.org/documentation/manpages/collectd-python.5.shtml

import sys
import time
from math import pi, sin

try:
    import collectd
    import logging

    logging.basicConfig(level=logging.INFO)
except ImportError:
    try:
        import dummy_collectd as collectd
    except:
        pass

PLUGIN_NAME = 'hello-world'
FREQUENCY = 1.0
DATAPOINT_COUNT = 0
NOTIFICATION_COUNT = 0
PLUGIN_INSTANCE = "example[frequency=%s]"
SEND = True


def log(param):
    """
    Log messages to either collectd or stdout depending on how it was called.

    :param param: the message
    :return:  None
    """

    if __name__ != '__main__':
        collectd.info("%s: %s" % (PLUGIN_NAME, param))
    else:
        sys.stderr.write("%s\n" % param)


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

    for kv in conf.children:
        if kv.key == 'Frequency':
            global FREQUENCY
            FREQUENCY = float(kv.values[0])


def read():
    """
    This method has been registered as the read callback and will be called every polling interval
    to dispatch metrics.  We emit three metrics: one gauge, a sine wave; two counters for the
    number of datapoints and notifications we've seen.

    :return: None
    """

    val = sin(time.time() * 2 * pi / 60 * FREQUENCY)
    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="sine",
                    plugin_instance=PLUGIN_INSTANCE % FREQUENCY,
                    type="gauge",
                    values=[val]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="datapoints",
                    type="counter",
                    values=[DATAPOINT_COUNT]).dispatch()

    collectd.Values(plugin=PLUGIN_NAME,
                    type_instance="notifications",
                    type="counter",
                    values=[NOTIFICATION_COUNT]).dispatch()

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

    log("Plugin %s initializing..." % PLUGIN_NAME)


def shutdown():
    """
    This method has been registered as the shutdown callback. this gives the plugin a way to clean
    up after itself before shutting down.  We'll just log a message.

    :return: None
    """

    log("Plugin %s shutting down..." % PLUGIN_NAME)


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

    log("Plugin %s flushing timeout %s and identifier %s" % PLUGIN_NAME, timeout, identifier)


def log_cb(severity, message):
    """
    This method has been registered as the log callback. Don't emit log messages from within this
    as you will cause a loop.

    :param severity: an integer and small for important messages and high for less important messages
    :param message: a string without a newline at the end
    :return: None
    """

    pass


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
    collectd.register_read(read)
    collectd.register_init(init)
    collectd.register_shutdown(shutdown)
    collectd.register_write(write)
    collectd.register_flush(flush)
    collectd.register_log(log_cb)
    collectd.register_notification(notification)
else:
    # outside plugin just collect the info
    read()
    if len(sys.argv) < 2:
        while True:
            time.sleep(10)
            read()
