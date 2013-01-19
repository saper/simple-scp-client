#! /usr/bin/env python
# -*- coding: utf-8 -*-

#
# Trivial implementation of the scp/rcp
# protocol to fetch one file from the remote server
#
# Supports different SSH clients, like OpenSSH
# and Simon Tatham's plink.exe
#
# Marcin Cieślak <saper@saper.info> 2013
#

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
    nul = "\0"
    try:
        p.stdin.write(nul)
        stat = p.stdout.read(1)
        if stat:
            if stat != "C":
                raise RemoteFileNotFoundError(p.stdout.readline())
            filemode = p.stdout.readline()
            (mode, length, fname) = filemode.split()
            p.stdin.write(nul)
            contents = p.stdout.read(int(length))
            p.stdin.write(nul)
        else:
            raise CannotCopyFileError(p.stderr.read())
    except IOError:
        raise CannotCopyFileError(p.stderr.read())
    p.wait()
    p.stdin.close()
    p.stdout.close()
    p.stderr.close()
    return contents


if __name__ == '__main__':
    import sys
    import os
    from getopt import getopt

    (opts, args) = getopt(sys.argv[1:], "p:")
    port = None
    for (opt, val) in opts:
        if opt == '-p':
            port = val

    if len(args) < 1:
        sys.stderr.write("usage: %s [-p port] user@hostname\n" % sys.argv[0])
        sys.exit(1)

    sys.stdout.write(remote_copy(secure_shell(os.getenv("GIT_SSH") or "ssh",
                                 port, args[0], "scp", "-f",
                                 "hooks/commit-msg")))
