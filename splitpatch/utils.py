#!/usr/bin/env python

import glob
import email
import random
import re
import cPickle as pickle

group1 = ['src/storage/','src/qemu/qemu_blockjob.c']
group2 = ['src/network/','src/cpu/','src/interface/', 'src/node_device/','src/nwfilter/','src/util/virnuma.c',]
group3 = ['src/security/','src/qemu/qemu_agent.c','src/qemu/qemu_migration.c','src/logging/']

mailfile = glob.glob('/root/libvirtmail/*')
dataset = '/root/patch-dataset.txt'

def loaddatasetfromtxt(filename=dataset):
    fd = open(filename)
    msg = fd.read()
    fd.close()
    retdict = {}

    for line in msg.splitlines():
        groupinfo = line.split(' - ')[-1]
        subject = line[:line.find(groupinfo) - 3]
        retgroup = int(groupinfo.replace('group','').split()[0])
        retdict[subject] = retgroup

    return retdict

def parsemail(mailfilelist=mailfile):
    retdict = {}

    for mail in mailfilelist:
        fd = open(mail)
        msg = email.message_from_file(fd)
        fd.close()
        subject = msg['Subject'].__str__()
        if 'PATCH' not in subject:
            continue

        if '\r\n\t' in subject:
            subject = subject.replace('\r\n\t', ' ')
        if '\r\n' in subject:
            subject = subject.replace('\r\n', '')

        tmpstr = subject[subject.find("PATCH"):]
        subject = tmpstr[tmpstr.find(']') + 2:]

        main = ''
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                main += part.get_payload(decode=True)

        retdict[subject] = main

    return retdict

def getinfo(msg, detail=None, subpatch=None):
    retlist = []
    patchdetail = False
    normalpatch = False
    for line in msg.splitlines():
        if line == '':
            continue

        if line[:14] == "Signed-off-by:":
            retlist.append(line[15: line.find('<') - 1])
            continue

        if line == '---':
            patchdetail = True
            continue

        if line == '--' or line == '-- ':
            break

        if patchdetail:
            if line[:10] == 'diff --git':
                normalpatch = True
                break

            if re.match('^ \S+[ ]+\|[ ]+[0-9]+ [\+\-]+$', line):
                retlist.append(line.split('|')[0].split()[0])
                if detail is not None:
                    filename = line.split('|')[0].split()[0]
                    number = line.split('|')[1].split()[0]
                    detail[filename] = int(number)
                continue
        else:
            if re.match('^ \S+[ ]+\|[ ]+[0-9]+ [\+\-]+$', line):
                retlist.append(line.split('|')[0].split()[0])
                if detail is not None:
                    filename = line.split('|')[0].split()[0]
                    number = line.split('|')[1].split()[0]
                    detail[filename] = int(number)
                continue

            tmpline = line.replace('.', '').replace(',', '').replace(':', '')
            for n in tmpline.split():
                if n != '':
                    retlist.append(n)

    if normalpatch == False and subpatch is not None:
        startparse = False
        for line in msg.splitlines():
            if re.match('^[^\(]+\([0-9]+\):$', line):
                startparse = True
                continue

            if startparse:
                if line == '':
                    startparse = False
                    continue

                if line[:3] != '   ':
                    subpatch.append(line[2:])
                else:
                    """ it is a part of last patch name"""
                    tmpstr = subpatch.pop()
                    subpatch.append('%s%s' % (tmpstr, line[3:]))

    return retlist

def manualsplit(msg):
    detail = {}
    getinfo(msg, detail)
    if detail == {}:
        return

    maxchange = [0, None]
    for n in detail.keys():
        if maxchange[0] < detail[n]:
            maxchange[0] = detail[n]
            maxchange[1] = n

    if maxchange[1] == None:
        print detail
        return

    for n in group1:
        if n in maxchange[1]:
            return 1
    for n in group2:
        if n in maxchange[1]:
            return 2
    for n in group3:
        if n in maxchange[1]:
            return 3

def savedata(filepath, data):
    f1 = file(filepath, 'wb')  
    pickle.dump(data, f1, True)
    f1.close()

def loaddata(filepath):
    f1 = file(filepath, 'rb')  
    return pickle.load(f1)

if __name__ == '__main__':
    parsemail()
    loaddatasetfromtxt()
    print 'pass'
