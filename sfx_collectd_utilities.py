import logging

try:
    import collectd
except ImportError:
    try:
        import dummy_collectd as collectd
    except:
        pass

NOTIF_FAILURE = collectd.NOTIF_FAILURE
NOTIF_WARNING = collectd.NOTIF_WARNING
NOTIF_OKAY = collectd.NOTIF_OKAY


# TODO: @charlie add tls authentication for making requests


# TODO: @charlie add functions for managing versioned metrics


class CollectdLogHandler(logging.Handler):
    """Log handler to forward statements to collectd
    A custom log handler that forwards log messages raised
    at level debug, info, notice, warning, and error
    to collectd's built in logging.  Suppresses extraneous
    info and debug statements using a "verbose" boolean
    Inherits from logging.Handler
    Arguments
        plugin -- name of the plugin (default 'unknown')
        verbose -- enable/disable verbose messages (default False)
    """

    def __init__(self, plugin="unknown", verbose=False):
        """Initializes CollectdLogHandler
        Arguments
            plugin -- string name of the plugin (default 'unknown')
            verbose -- enable/disable verbose messages (default False)
        """
        self.verbose = verbose
        self.plugin = plugin
        logging.Handler.__init__(self, level=logging.NOTSET)

    def emit(self, record):
        """
        Emits a log record to the appropriate collectd log function
        Arguments
        record -- str log record to be emitted
        """
        if record.msg is not None:
            if record.levelname == 'ERROR':
                collectd.error('%s : %s' % (self.plugin, record.msg))
            elif record.levelname == 'WARNING':
                collectd.warning('%s : %s' % (self.plugin, record.msg))
            elif record.levelname == 'NOTICE':
                collectd.notice('%s : %s' % (self.plugin, record.msg))
            elif record.levelname == 'INFO':
                collectd.info('%s : %s' % (self.plugin, record.msg))
            elif record.levelname == 'DEBUG':
                collectd.info('%s : %s' % (self.plugin, record.msg))


class CollectdLogger(logging.Logger):
    """Logs all collectd log levels via python's logging library
    Custom python logger that forwards log statements at
    level: debug, info, notice, warning, error
    Inherits from logging.Logger
    Arguments
    name -- name of the logger
    level -- log level to filter by
    """

    def __init__(self, name, level=logging.INFO):
        """Initializes CollectdLogger
        Arguments
        name -- name of the logger
        level -- log level to filter by
        """
        logging.Logger.__init__(self, name, level)
        logging.addLevelName(25, 'NOTICE')
        handle = CollectdLogHandler(name)
        self.propagate = False
        self.addHandler(handle)

    def notice(self, msg):
        """Logs a 'NOTICE' level statement at level 25
        Arguments
        msg - log statement to be logged as 'NOTICE'
        """
        self.log(25, msg)


# assign the custom CollectdLogger to be the default logging class
logging.setLoggerClass(CollectdLogger)


def get_log_level_from_config(val):
    """Takes a config value and maps it to a log level
    Default Value: logging.INFO
    """
    # normalize the value
    value = str(val).upper()
    log_level = logging.INFO
    if value == 'DEBUG':
        log_level = logging.DEBUG
    elif value == 'INFO':
        log_level = logging.INFO
    elif value == 'NOTICE':
        # NOTICE is a custom level in sfx_utilities.CollectdLogger
        log_level = 25
    elif value == 'WARNING':
        log_level = logging.WARNING
    elif value == 'ERROR':
        log_level = logging.ERROR
    return log_level


def str_to_bool(flag):
    """Converts true/false to boolean"""
    flag = str(flag).strip().lower()
    if flag == 'true':
        return True
    elif flag != 'false':
        collectd.warning("WARNING: REQUIRES BOOLEAN. \
                RECEIVED %s. ASSUMING FALSE." % (str(flag)))

    return False


def _parse_dimensions(dimensions={}, max_length=1022):
    """Formats a dictionary of key/value pairs as a comma-delimited list of
    key=value tokens."""
    if dimensions:
        return ','.join(['='.join(p) for p in dimensions.items()])[:(max_length)]
    else:
        return ''


def isValidDimensionKey():
    """
    Returns True if the string is a valid dimension key or False if it is not
    """
    isValid = True
    return isValid


# host, plugin, plugin_instance, time, type, type_instance
def dispatch_notification(message="", severity=NOTIF_OKAY,
                          plugin="Unknown", plugin_instance="",
                          type="objects", type_instance=None,
                          time=None, host=None):
    """
    This method dispatches notifications and appropriately appends dimensions to plugin instance

    Keyword arguments:
    message --  message attached to the event describing what
                happened (default "")

    severity -- severity of the notification
                [NOTIF_OKAY, NOTIF_WARNING, NOTIF_FAILURE] (default NOTIF_OKAY)

    plugin -- identifies the plugin emitting the notification (default "Unknown")

    plugin_instance -- identifies the plugin instance (default "")

    type -- identifies the type of the notification (default "objects")

    type_instance -- type instance string (default None)

    time -- the time associated with the notification.  Typically, this should not be set.
            collectd will assign a time if one is not provided (default None)

    host -- the hostname associated with the notification.  Typically, this should not be set.
            collectd will assign a hostname when one is not provided (default None)
    """
    notif = collectd.Notification(plugin=plugin,
                                  plugin_instance=plugin_instance,
                                  message=message,
                                  type=type)
    if severity in [NOTIF_FAILURE, NOTIF_OKAY, NOTIF_WARNING]:
        notif.severity = severity
    else:
        raise Exception(("Unable to parse notification severity {}. "
                         "Valid options are NOTIF_OKAY, NOTIF_WARNING, or NOTIF_FAILURE").format(severity))
    if type_instance:  # type instance may be left empty
        notif.type_instance = type_instance
    if host:  # host is something that should just be set by collectd
        notif.host = host
    if time:  # will be set by collectd unless specified
        notif.time = time

    notif.dispatch()


def dispatch_values(values=None, dimensions={},
                    plugin="Unknown", plugin_instance="",
                    type="objects", type_instance=None,
                    plugin_instance_max_length=1024,
                    time=None, host=None, interval=None):
    """
    Keyword arguments:
    values --  a list of values to be emitted (default None)

    dimensions -- severity of the notification
                [NOTIF_OKAY, NOTIF_WARNING, NOTIF_FAILURE] (default NOTIF_OKAY)

    plugin -- identifies the plugin emitting the notification (default "Unknown")

    plugin_instance -- identifies the plugin instance (default "")

    type -- identifies the type of the notification (default "objects")

    type_instance -- type instance string (default None)

    plugin_instance_max_length -- maximum plugin_instance length for the collectd version (default 1024)

    time -- the time associated with the notification.  Typically, this should not be set.
            collectd will assign a time if one is not provided (default None)

    host -- the hostname associated with the notification.  Typically, this should not be set.
            collectd will assign a hostname when one is not provided (default None)
    """

    value = collectd.Values()

    if dimensions:
        # currently ingest parses dimensions out of the plugin_instance
        value.plugin_instance += '[{dims}]'.format(
            dims=_parse_dimensions(dimensions, max_length=(plugin_instance_max_length-len(plugin_instance)-2)))
        value.meta = dimensions
    else:
        # With some versions of CollectD, a dummy metadata map must to be added
        # to each value for it to be correctly serialized to JSON by the
        # write_http plugin. See
        # https://github.com/collectd/collectd/issues/716
        value.meta = {'true': 'true'}

    if type_instance:  # type instance may be left empty
        value.type_instance = type_instance
    if host:  # host is something that should just be set by collectd
        value.host = host
    if time:  # will be set by collectd unless specified
        value.time = time
    value.dispatch()
