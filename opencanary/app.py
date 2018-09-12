from __future__ import absolute_import, print_function, unicode_literals
__metaclass__ = type

import itertools
from pkg_resources import iter_entry_points
import platform
import traceback

from twisted.application import service
from twisted.application import internet
from twisted.application.app import startApplication
from twisted.internet import reactor
from twisted.internet.protocol import Factory

from daemonocle import Daemon

from .config import config
from .logger import getLogger
from .modules.http import CanaryHTTP
from .modules.ftp import CanaryFTP
from .modules.ssh import CanarySSH
from .modules.telnet import Telnet
from .modules.httpproxy import HTTPProxy
from .modules.mysql import CanaryMySQL
from .modules.mssql import MSSQL
from .modules.ntp import CanaryNtp
from .modules.tftp import CanaryTftp
from .modules.vnc import CanaryVNC
from .modules.sip import CanarySIP

#from .modules.example0 import CanaryExample0
#from .modules.example1 import CanaryExample1


ENTRYPOINT = "canary.usermodule"


def get_stdlib_modules():
    modules = [Telnet, CanaryHTTP, CanaryFTP, CanarySSH, HTTPProxy, CanaryMySQL,
               MSSQL, CanaryVNC, CanaryTftp, CanaryNtp, CanarySIP]
               #CanaryExample0, CanaryExample1]
    try:
        #Module needs RDP, but the rest of OpenCanary doesn't
        from .modules.rdp import CanaryRDP
        modules.append(CanaryRDP)
    except ImportError:
        pass


    try:
        #Module need Scapy, but the rest of OpenCanary doesn't
        from .modules.snmp import CanarySNMP
        modules.append(CanarySNMP)
    except ImportError:
        pass

    # NB: imports below depend on inotify, only available on linux
    if platform.system() == 'Linux':
        from .modules.samba import CanarySamba
        from .modules.portscan import CanaryPortscan
        modules.append(CanarySamba)
        modules.append(CanaryPortscan)

    return modules


logger = getLogger(config)


def start_mod(application, klass):
    try:
        obj = klass(config=config, logger=logger)
    except Exception as e:
        err = 'Failed to instantiate instance of class %s in %s. %s' % (
            klass.__name__,
            klass.__module__,
            traceback.format_exc()
        )
        logMsg({'logdata': err})
        return

    if hasattr(obj, 'startYourEngines'):
        try:
            obj.startYourEngines()
            msg = 'Ran startYourEngines on class %s in %s' % (
                klass.__name__,
                klass.__module__
                )
            logMsg({'logdata': msg})

        except Exception as e:
            err = 'Failed to run startYourEngines on %s in %s. %s' % (
                klass.__name__,
                klass.__module__,
                traceback.format_exc()
            )
            logMsg({'logdata': err})
    elif hasattr(obj, 'getService'):
        try:
            service = obj.getService()
            service.setServiceParent(application)
            msg = 'Added service from class %s in %s to fake' % (
                klass.__name__,
                klass.__module__
                )
            logMsg({'logdata': msg})
        except Exception as e:
            err = 'Failed to add service from class %s in %s. %s' % (
                klass.__name__,
                klass.__module__,
                traceback.format_exc()
            )
            logMsg({'logdata': err})
    else:
        err = 'The class %s in %s does not have any required starting method.' % (
            klass.__name__,
            klass.__module__
        )
        logMsg({'logdata': err})


def logMsg(msg):
    data = {}
#    data['src_host'] = device_name
#    data['dst_host'] = node_id
    data['logdata'] = {'msg': msg}
    logger.log(data, retry=False)


def load_external_modules():
    # Add all custom modules
    # (Permanently enabled as they don't officially use settings yet)
    for ep in iter_entry_points(ENTRYPOINT):
        try:
            klass = ep.load(require=False)
            yield klass
        except Exception as e:
            err = 'Failed to load class from the entrypoint: %s. %s' % (
                str(ep),
                traceback.format_exc()
                )
            logMsg({'logdata': err})


def extract_enabled_modules(external_modules, stdlib_modules, config):
    # Add only enabled modules
    return (
        m for m in itertools.chain(external_modules, stdlib_modules)
        if config.moduleEnabled(m.NAME)
    )


def setup_modules(app, mods):
    for klass in mods:
        start_mod(app, klass)


def initialize_app(name, config):
    app = service.Application(name)

    std_modules = get_stdlib_modules()
    ext_modules = load_external_modules()
    enabled_modules = extract_enabled_modules(ext_modules, std_modules, config)
    setup_modules(app, enabled_modules)

    return app


def run_twisted_app():
    app = initialize_app('opencanaryd', config)
    startApplication(app, 0)

    logMsg('Canary running!!!')
    reactor.run()


def get_app_daemon(pid_file):
    # FIXME: figure out the log prefix (opencanaryd)
    return Daemon(worker=run_twisted_app, pidfile=pid_file)
