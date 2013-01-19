#! /usr/bin/env python
import unittest
import re

from scp import secure_shell, remote_copy,\
    CannotCopyFileError, RemoteFileNotFoundError

#TEST_CLIENTS = [ "ssh", "plink", "C:\\Program Files\\Git\\Bin\\ssh.exe" ]
TEST_CLIENTS = ["ssh"]
# Must not resolve
UNKNOWN_HOST = "zz.saper.info"
CLOSED_SSH_PORT = 2222

# Normal UNIX shell server to connect (not gerrit)
SHELL_HOST = "l.saper.info"
SHELL_SSH_PORT = 22
SHELL_USERNAME = "saper"

# Gerrit server coordinates
GERRIT_HOST = "l.saper.info"
GERRIT_SSH_PORT = 29418
GERRIT_USERNAME = "saper"
WRONG_USERNAME = "wrong"
SHELL_DIRECTORY = ".ssh"


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
                          "scp", "-z", "hooks/wrong")

    def testGitHook(self):
        f = self.run_scp(GERRIT_SSH_PORT, "%s@%s" %
                         (GERRIT_USERNAME, GERRIT_HOST),
                         "scp", "-f", "hooks/commit-msg")
        SH = re.compile(".*/bin/sh.*")
        self.assert_(SH.match(f.split()[0]))

if __name__ == "__main__":
    for test_client in TEST_CLIENTS:
        unittest.main()
