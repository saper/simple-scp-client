#! /usr/bin/env python
import subprocess
import re

TEST_CLIENT = "ssh"

test = [
    # CannotCopyFileError
    (TEST_CLIENT, 22, "saper@zz.saper.info", "scp", "-f", "hooks/wrong"),
    # RemoteFileNotFoundError
    (TEST_CLIENT, 22, "saper@l.saper.info", "scp", "-f", "hooks/wrong"),
    # CannotCopyFileError
    (TEST_CLIENT, 2222, "saper@l.saper.info", "scp", "-f", "hooks/wrong"),
    # CannotCopyFileError
    (TEST_CLIENT, 29418, "wrong@l.saper.info", "scp", "-f", "hooks/wrong"),
    # CannotCopyFileError
    (TEST_CLIENT, 29418, "saper@l.saper.info", "xscp", "-f", "hooks/wrong"),
    # RemoteFileNotFoundError
    (TEST_CLIENT, 29418, "saper@l.saper.info", "scp", "-z", "hooks/wrong"),
    # RemoteFileNotFoundError
    (TEST_CLIENT, 29418, "saper@l.saper.info", "scp", "-f", "hooks/wrong"),
    # OK
    (TEST_CLIENT, 29418, "saper@l.saper.info", "scp", "-f", "hooks/commit-msg")
]


SSH_CLIENTS = [
    (re.compile("plink", re.I), "-P %s", "%s"),
    (re.compile("ssh", re.I), "-p %s", "%s")
]


class UnknownSSHClientError(Exception):
    pass


class SecureCopyError(Exception):
    pass


class CannotCopyFileError(SecureCopyError):
    pass


class RemoteFileNotFoundError(SecureCopyError):
    pass


def secure_shell(cmd, port, userhost, *argv):
    conn = None
    for (pattern, PORT, USERHOST) in SSH_CLIENTS:
        if re.search(pattern, cmd):
            if port:
                conn = (cmd, PORT % port, USERHOST % userhost) + argv
            else:
                conn = (cmd, USERHOST % userhost) + argv

    if conn:
        p = subprocess.Popen(conn + argv,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        return p
    else:
        raise UnknownSSHClientError(cmd)


def remote_copy(p):
    try:
        p.stdin.write("\0")
        filemode = p.stdout.readline()
        if filemode:
            if filemode[0] != 'C':
                raise RemoteFileNotFoundError(filemode[1:])
            (mode, length, fname) = filemode.split()
            p.stdin.write("\0")
            contents = p.stdout.read(int(length))
            p.stdin.write("\0")
        else:
            raise CannotCopyFileError(p.stderr.readline())
    except IOError:
        raise CannotCopyFileError(p.stderr.readline())
    return contents


if __name__ == "__main__":
    for argv in test:
        try:
            print(remote_copy(secure_shell(*argv)))
        except Exception as e:
            print(repr(e))
