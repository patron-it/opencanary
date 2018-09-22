from opencanary.modules import CanaryService
from opencanary.modules import FileSystemWatcher
import os
import re

class SynLogWatcher(FileSystemWatcher):
    def __init__(self, logger=None, logFile=None):
        self.logger = logger
        #print ('SynLogWatcher started')
        FileSystemWatcher.__init__(self, fileName=logFile)

    def handleLines(self, lines=None):
        for line in lines:
            try:
                (rubbish, log) = line.split('canaryfw: ')
            except ValueError:
                continue
            tags = log.split(' ')
            kv = {}
            for tag in tags:
                if tag.find('=') >= 0:
                    (key, val) = tag.split('=')
                else:
                    key = tag
                    val = ''
                kv[key]=val

            data = {}
            data['src_host'] = kv.pop('SRC')
            data['src_port'] = kv.pop('SPT')
            data['dst_host'] = kv.pop('DST')
            data['dst_port'] = kv.pop('DPT')
            data['logtype']  = self.logger.LOG_PORT_SYN
            data['logdata']  = kv
            self.logger.log(data)

class CanaryPortscan(CanaryService):
    NAME = 'portscan'

    def __init__(self,config=None, logger=None):
        CanaryService.__init__(self, config=config, logger=logger)
        self.audit_file = config.getVal('portscan.logfile', default='/var/log/kern.log')
        self.synrate = int(config.getVal('portscan.synrate', default=5))
        self.listen_addr = config.getVal('device.listen_addr', default='')
        self.listen_interface = config.getVal('device.listen_interface', default='')
        self.config = config

    def startYourEngines(self, reactor=None):
        iptables_args = {
            'dst': (
                ('--destination ' + self.listen_addr)
                if len(self.listen_addr)
                else ''
            ),
            'interface': (
                ('-i ' + self.listen_interface)
                if len(self.listen_interface)
                else ''
            ),
            'synrate': self.synrate,
        }

        iptables_cmd_tmpl = (  # FIXME: get rid of `sudo`
            'sudo /sbin/iptables -t mangle -{{action_flag}} PREROUTING '
            '-p tcp {dst} {interface} --syn '
            '-j LOG --log-level=warning --log-prefix="canaryfw: " '
            '-m limit --limit="{synrate}/second"'
        )
        iptables_pre_cmd_tmpl = iptables_cmd_tmpl.format(**iptables_args)

        os.system(iptables_pre_cmd_tmpl.format(action_flag='D'))
        os.system(iptables_pre_cmd_tmpl.format(action_flag='A'))

        fs = SynLogWatcher(logFile=self.audit_file, logger=self.logger)
        fs.start()

    def configUpdated(self,):
        pass
