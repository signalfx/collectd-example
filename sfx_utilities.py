import logging

try:
    import collectd

except ImportError:
    try:
        import dummy_collectd as collectd
    except:
        pass


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


def getLogLevelFromConfig(val):
    """Takes a config value and maps it to a log level
    Default Value: logging.INFO
    """
    log_level = logging.INFO
    if val == 'DEBUG':
        log_level = logging.DEBUG
    elif val == 'INFO':
        log_level = logging.INFO
    elif val == 'NOTICE':
        # NOTICE is a custom level in sfx_utilities.CollectdLogger
        log_level = 25 
    elif val == 'WARNING':
        log_level = logging.WARNING
    elif val == 'ERROR':
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
    

# def shutdown(name):
#     """Cleanup on plugin shutdown."""
#     lg = logging.getLogger(name)

#     for key, logger in logging.manager.loggerDict.items():
#         collectd.info("Attempting to shutdown logger %s" % logger)
#         for handle in logger.handlers.items():
#             pass


#     """
#     For some reason handlers seem to leak memory, so we need to expicitly
#     destroy references to them
#      """
    
#     lg.info("{} shutting down".format(name))
#     for handle in lg.handlers:
#         lg.removeHandler(handle)