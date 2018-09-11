from __future__ import absolute_import, print_function, unicode_literals
__metaclass__ = type

from pkg_resources import iter_entry_points
import traceback

from twisted.application import service
from twisted.application import internet
from twisted.application.app import startApplication
from twisted.internet import reactor
from twisted.internet.protocol import Factory

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
MODULES = [Telnet, CanaryHTTP, CanaryFTP, CanarySSH, HTTPProxy, CanaryMySQL,
           MSSQL, CanaryVNC, CanaryTftp, CanaryNtp, CanarySIP]
           #CanaryExample0, CanaryExample1]
try:
    #Module needs RDP, but the rest of OpenCanary doesn't
    from opencanary.modules.rdp import CanaryRDP
    MODULES.append(CanaryRDP)
except ImportError:
    pass


try:
    #Module need Scapy, but the rest of OpenCanary doesn't
    from opencanary.modules.snmp import CanarySNMP
    MODULES.append(CanarySNMP)
except ImportError:
    pass

# NB: imports below depend on inotify, only available on linux
import sys
if sys.platform.startswith("linux"):
    from opencanary.modules.samba import CanarySamba
    from opencanary.modules.portscan import CanaryPortscan
    MODULES.append(CanarySamba)
    MODULES.append(CanaryPortscan)

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

application = service.Application("opencanaryd")

# List of modules to start
start_modules = []

# Add all custom modules
# (Permanently enabled as they don't officially use settings yet)
for ep in iter_entry_points(ENTRYPOINT):
    try:
        klass = ep.load(require=False)
        start_modules.append(klass)
    except Exception as e:
        err = 'Failed to load class from the entrypoint: %s. %s' % (
            str(ep),
            traceback.format_exc()
            )
        logMsg({'logdata': err})

# Add only enabled modules
start_modules.extend(filter(lambda m: config.moduleEnabled(m.NAME), MODULES))

for klass in start_modules:
    start_mod(application, klass)

logMsg("Canary running!!!")


def run_twisted_app(app):
    startApplication(app, 0)
    reactor.run()
