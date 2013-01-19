#! /usr/bin/env python
import subprocess
import re


SSH_CLIENTS = [
    (re.compile("plink", re.I),
        lambda p: ("-P", "%s" % p,),
        lambda uh: ("%s" % uh,)),
    (re.compile("ssh", re.I),
        lambda p: ("-p %s" % p,),
        lambda uh: ("%s" % uh,))
]


class SSHError(Exception):
    pass


class UnknownSSHClientError(SSHError):
    pass


class SecureCopyError(SSHError):
    pass


class CannotCopyFileError(SecureCopyError):
    pass


class RemoteFileNotFoundError(SecureCopyError):
    pass


def secure_shell(cmd, port, userhost, *argv):
    conn = None
    for (pattern, PORT, USERHOST) in SSH_CLIENTS:
        if re.search(pattern, cmd):
            conn = [cmd]
            if port:
                conn += PORT(port)
            conn += USERHOST(userhost)

    if conn:
        p = subprocess.Popen(conn + list(argv),
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
