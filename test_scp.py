#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Simple test suite for scp implementation
#
# Marcin Cieślak <saper@saper.info> 2013
import unittest
import re

from scp import secure_shell, remote_copy,\
    CannotCopyFileError, RemoteFileNotFoundError

#
# List of SSH clients to run the test suite against
# Make sure proper authentication is available (for example,
# ssh-agent or pageant)
#
#TEST_CLIENTS = [ "ssh", "plink", "C:\\Program Files\\Git\\Bin\\ssh.exe" ]
TEST_CLIENTS = ["ssh"]
# Host name that must not resolve
UNKNOWN_HOST = "zz.saper.info"

# Normal UNIX shell server to connect (not gerrit)
# This is used to test response to normal
# (usually OpenSSH) implementation - file not found
# or directory instead of the file
SHELL_HOST = "l.saper.info"
SHELL_SSH_PORT = 22
SHELL_USERNAME = "saper"
# The directory below has to exist on SHELL_HOST
# under SHELL_USERNAME account
SHELL_DIRECTORY = ".ssh"
# TCP port that should be closed on SHELL_HOST
CLOSED_SSH_PORT = 2222

# Gerrit server coordinates
GERRIT_HOST = "review.openstack.org"
GERRIT_SSH_PORT = 29418
GERRIT_USERNAME = "saperski"
# Incorrect username on GERRIT_HOST
WRONG_USERNAME = "wrong"


class SimpleSCPClientTestCase(unittest.TestCase):

    def run_scp(self, *argv):
        argv = tuple((test_client,) + argv)
        return remote_copy(secure_shell(*argv))

    def testUknownHost(self):
        self.assertRaises(CannotCopyFileError, self.run_scp,
                          SHELL_SSH_PORT, UNKNOWN_HOST,
                          "scp", "-f", "hooks/wrong")

    def testConnectionRefused(self):
        self.assertRaises(CannotCopyFileError, self.run_scp,
                          CLOSED_SSH_PORT, UNKNOWN_HOST,
                          "scp", "-f", "hooks/wrong")

    def testNoSuchFile(self):
        self.assertRaises(RemoteFileNotFoundError, self.run_scp,
                          SHELL_SSH_PORT,
                          "%s@%s" % (SHELL_USERNAME, SHELL_HOST),
                          "scp", "-f", "hooks/wrong")

    def testDirectoryFile(self):
        self.assertRaises(RemoteFileNotFoundError, self.run_scp,
                          SHELL_SSH_PORT,
                          "%s@%s" % (SHELL_USERNAME, SHELL_HOST),
                          "scp", "-f", SHELL_DIRECTORY)

    def testWrongUserName(self):
        self.assertRaises(CannotCopyFileError, self.run_scp,
                          GERRIT_SSH_PORT,
                          "%s@%s" % (WRONG_USERNAME, GERRIT_HOST),
                          "scp", "-f", "hooks/wrong")

    def testWrongCommand(self):
        self.assertRaises(CannotCopyFileError, self.run_scp,
                          GERRIT_SSH_PORT,
                          "%s@%s" % (GERRIT_USERNAME, GERRIT_HOST),
                          "xscp", "-f", "hooks/wrong")

    def testIllegalArgument(self):
        self.assertRaises(RemoteFileNotFoundError, self.run_scp,
                          GERRIT_SSH_PORT,
                          "%s@%s" % (GERRIT_USERNAME, GERRIT_HOST),
                          "scp", "-z", "hooks/wrong")

    def testWrongFileName(self):
        self.assertRaises(RemoteFileNotFoundError, self.run_scp,
                          GERRIT_SSH_PORT,
                          "%s@%s" % (GERRIT_USERNAME, GERRIT_HOST),
                          "scp", "-f", "hooks/wrong")

    def testGitHook(self):
        f = self.run_scp(GERRIT_SSH_PORT, "%s@%s" %
                         (GERRIT_USERNAME, GERRIT_HOST),
                         "scp", "-f", "hooks/commit-msg")
        SH = re.compile(".*/bin/sh.*")
        self.assert_(SH.match(f.split()[0]))

if __name__ == "__main__":
    for test_client in TEST_CLIENTS:
        unittest.main()
