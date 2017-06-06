"""
This module assumes that OpenCanary has been installed and is running with the
default settings.

In particular it assumes that OpenCanary is logging to /var/tmp/opencanary.log

It would be much better to setup tests to start the services needed and provide
the configuration files so that tests can be run witout needing to reinstall
and start the service before each test. It would also be better to be able to
test the code directly rather than relying on the out put of loggs.

Still this is a start.
"""

import json
from ftplib import FTP, error_perm
import unittest

# These libraries are only needed by the test suite and so aren't in the
# OpenCanary requirements, there is a requirements.txt file in the tests folder
# Simply run `pip install -r opencanary/test/requirements.txt`
import requests
import paramiko


def get_last_log():
    """
    Gets the last line from `/var/tmp/opencanary.log` as a dictionary
    """
    with open('/var/tmp/opencanary.log', 'r') as log_file:
        return json.loads(log_file.readlines()[-1])


class TestFTPModule(unittest.TestCase):
    """
    Tests the cases for the FTP module.

    The FTP server should not allow logins and should log each attempt.
    """
    def setUp(self):
        self.ftp = FTP('localhost')

    def test_anonymous_ftp(self):
        """
        Try to connect to the FTP service with no username or password.
        """
        self.assertRaises(error_perm, self.ftp.login)
        log = get_last_log()
        self.assertEqual(log['dst_port'], 21)
        self.assertEqual(log['logdata']['USERNAME'], "anonymous")
        self.assertEqual(log['logdata']['PASSWORD'], "anonymous@")

    def test_authenticated_ftp(self):
        """
        Connect to the FTP service with a test username and password.
        """
        self.assertRaises(error_perm,
                          self.ftp.login,
                          user='test_user',
                          passwd='test_pass')
        last_log = get_last_log()
        self.assertEqual(last_log['dst_port'], 21)
        self.assertEqual(last_log['logdata']['USERNAME'], "test_user")
        self.assertEqual(last_log['logdata']['PASSWORD'], "test_pass")

    def tearDown(self):
        self.ftp.close()


class TestHTTPModule(unittest.TestCase):
    """
    Tests the cases for the HTTP module.

    The HTTP server should look like a NAS and present a login box, any
    interaction with the server (GET, POST) should be logged.
    """
    def test_get_http_home_page(self):
        """
        Simply get the home page.
        """
        request = requests.get('http://localhost/')
        self.assertEqual(request.status_code, 200)
        self.assertIn('Synology RackStation', request.text)
        last_log = get_last_log()
        self.assertEqual(last_log['dst_port'], 80)
        self.assertEqual(last_log['logdata']['HOSTNAME'], "localhost")
        self.assertEqual(last_log['logdata']['PATH'], "/index.html")
        self.assertIn('python-requests', last_log['logdata']['USERAGENT'])

    def test_log_in_to_http_with_basic_auth(self):
        """
        Try to log into the site with basic auth.
        """
        request = requests.post('http://localhost/', auth=('user', 'pass'))
        # Currently the web server returns 200, but in future it should return
        # a 403 statuse code.
        self.assertEqual(request.status_code, 200)
        self.assertIn('Synology RackStation', request.text)
        last_log = get_last_log()
        self.assertEqual(last_log['dst_port'], 80)
        self.assertEqual(last_log['logdata']['HOSTNAME'], "localhost")
        self.assertEqual(last_log['logdata']['PATH'], "/index.html")
        self.assertIn('python-requests', last_log['logdata']['USERAGENT'])
        # OpenCanary doesn't currently record credentials from basic auth.

    def test_log_in_to_http_with_parameters(self):
        """
        Try to log into the site by posting the parameters
        """
        login_data = {
            'username': 'test_user',
            'password': 'test_pass',
            'OTPcode': '',
            'rememberme': '',
            '__cIpHeRtExt': '',
            'isIframeLogin': 'yes'}
        request = requests.post('http://localhost/index.html', data=login_data)
        # Currently the web server returns 200, but in future it should return
        # a 403 statuse code.
        self.assertEqual(request.status_code, 200)
        self.assertIn('Synology RackStation', request.text)
        last_log = get_last_log()
        self.assertEqual(last_log['dst_port'], 80)
        self.assertEqual(last_log['logdata']['HOSTNAME'], "localhost")
        self.assertEqual(last_log['logdata']['PATH'], "/index.html")
        self.assertIn('python-requests', last_log['logdata']['USERAGENT'])
        self.assertEqual(last_log['logdata']['USERNAME'], "test_user")
        self.assertEqual(last_log['logdata']['PASSWORD'], "test_pass")


class TestSSHModule(unittest.TestCase):
    """
    Tests the cases for the SSH server
    """
    def setUp(self):
        self.connection = paramiko.SSHClient()
        self.connection.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def test_ssh_with_basic_login(self):
        """
        Try to log into the SSH server
        """
        self.assertRaises(paramiko.ssh_exception.AuthenticationException,
                          self.connection.connect,
                          hostname="localhost",
                          port=8022,
                          username="test_user",
                          password="test_pass")
        last_log = get_last_log()
        self.assertEqual(last_log['dst_port'], 8022)
        self.assertIn('paramiko', last_log['logdata']['REMOTEVERSION'])
        self.assertEqual(last_log['logdata']['USERNAME'], "test_user")
        self.assertEqual(last_log['logdata']['PASSWORD'], "test_pass")

    def tearDown(self):
        self.connection.close()


if __name__ == '__main__':
    unittest.main()
