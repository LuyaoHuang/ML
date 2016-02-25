#!/usr/bin/env python

import random
import os
import math
import time
from utils import *
from nn import *

uselesslist = ['am','is','are','did','do', 'done','will','shall','would','should','to','on','for','at','in','we','i','my','mine','you','your','he','she','him','her','it',"it's",'however', 'which','where','of', 'the', 'a', 'an', 'about','above','under','after','by','with',"i'am","i'd","we're","they're"]

def traindata():
    print "Collect Info"
    targetdict = loaddatasetfromtxt()
    maildict = parsemail()

    print "Start gen dataset for training"

    strdict = {}
    strlist = [] # use for gen numpy
    traindataset = []
    verifydataset = []
    trainarray = []
    resultarray = []

    for i in targetdict.keys():
        if i not in maildict.keys():
            raise ValueError, 'cannot find %s' % i

        """ patch describe"""
        subpatch=[]
        tmplist = getinfo(maildict[i], subpatch=subpatch)
        if subpatch != []:
            for m in subpatch:
                if m not in maildict.keys():
                    print "not find %s" % m
                    continue
                tmplist = getinfo(maildict[m])

                for n in tmplist:
                    if n.lower() not in strdict.keys():
                        strdict[n.lower()] = 1
                    else:
                        strdict[n.lower()] += 1

                """ patch subject """
                for n in m.split():
                    tmp = n.replace(':', '')
                    if tmp.lower() not in strdict.keys():
                        strdict[tmp.lower()] = 1
                    else:
                        strdict[tmp.lower()] += 1

        else:
            for n in tmplist:
                if n.lower() not in strdict.keys():
                    strdict[n.lower()] = 1
                else:
                    strdict[n.lower()] += 1

            """ patch subject """
            for n in i.split():
                tmp = n.replace(':', '')
                if tmp.lower() not in strdict.keys():
                    strdict[tmp.lower()] = 1
                else:
                    strdict[tmp.lower()] += 1

        if random.random() < 0.2:
    #    if i in staticverifylist:
            verifydataset.append(i)
        else:
            traindataset.append(i)

    count = 0
    for i in maildict.keys():
        if i in targetdict.keys():
            continue

        groupinfo = manualsplit(maildict[i])
        if groupinfo is None:
            continue
        subpatch=[]
        tmplist = getinfo(maildict[i], subpatch=subpatch)
        if subpatch != []:
            continue

        targetdict[i] = groupinfo
        count += 1

        """ patch describe"""
        for n in tmplist:
            if n.lower() not in strdict.keys():
                strdict[n.lower()] = 1
            else:
                strdict[n.lower()] += 1

        """ patch subject """
        for n in i.split():
            tmp = n.replace(':', '')
            if tmp.lower() not in strdict.keys():
                strdict[tmp.lower()] = 1
            else:
                strdict[tmp.lower()] += 1

        traindataset.append(i)

    print "add %d new training case to dataset" % count
    #print 'srcdict is %d' % len(strdict)
    """ make it small """
    for n in strdict.keys():
        if n in uselesslist:
            continue

        if strdict[n] > 1:
            strlist.append(n)

    #print 'strlist is %d' % len(strlist)

    for n in traindataset:
        tmparray = []
        subpatch=[]
        tmplist = getinfo(maildict[n], subpatch=subpatch)
        if subpatch == []:
            for i in strlist:
                if i in tmplist:
                    tmparray.append(1.0)
                else:
                    tmparray.append(0.0)
        else:
            tmplist = []
            for m in subpatch:
                if m not in maildict.keys():
                    print "not find %s" % m
                    continue
                tmplist.extend(getinfo(maildict[m]))
            for i in strlist:
                if i in tmplist:
                    tmparray.append(1.0)
                else:
                    tmparray.append(0.0)

        trainarray.append(tmparray)

        if targetdict[n] == 3:
            resultarray.append([0,0,1])
        elif targetdict[n] == 2:
            resultarray.append([0,1,0])
        elif targetdict[n] == 1:
            resultarray.append([1,0,0])
        else:
            raise ValueError, 'there is no group %d' % targetdict[n]

    print "Start traning NN"
    x = numpy.array(trainarray)
    y = numpy.array(resultarray)
    x = x.T
    y = y.T
    max_iterations = 400

    starttime = time.time()
    nn = NN(x.shape[0], int(math.sqrt(x.shape[0] + y.shape[0])), y.shape[0], lamda=0.001)
    opt = scipy.optimize.minimize(nn.BPformin, nn.theta, 
                                  args = (x,y), method = 'L-BFGS-B',
                                  jac = True, options = {'maxiter': max_iterations})

    endtime = time.time()
    #print y
    #print nn.FPformin(x, opt.x)

    print "take %f second to train nn" % (endtime - starttime)
    print "start verify NN"
    verifyarray = []
    vresultarray = []
    for n in verifydataset:
        tmparray = []
        subpatch=[]
        tmplist = getinfo(maildict[n], subpatch=subpatch)
        if subpatch == []:
            for i in strlist:
                if i in tmplist:
                    tmparray.append(1.0)
                else:
                    tmparray.append(0.0)
        else:
            tmplist = []
            for m in subpatch:
                if m not in maildict.keys():
                    print "not find %s" % m
                    continue
                tmplist.extend(getinfo(maildict[m]))
            for i in strlist:
                if i in tmplist:
                    tmparray.append(1.0)
                else:
                    tmparray.append(0.0)


        verifyarray.append(tmparray)

        if targetdict[n] == 3:
            vresultarray.append([0,0,1])
        elif targetdict[n] == 2:
            vresultarray.append([0,1,0])
        elif targetdict[n] == 1:
            vresultarray.append([1,0,0])
        else:
            raise ValueError, 'there is no group %d' % targetdict[n]

    x = numpy.array(verifyarray)
    y = numpy.array(vresultarray)
    x = x.T

    #print y.T
    #print nn.FPformin(x, opt.x).T
    y2 = nn.FPformin(x, opt.x).T
    print "check %d verify case" % len(verifydataset)
    for n in range(len(y2)):
        maxv = y2[n].max()
        for i in range(len(y2[n])):
            if y2[n][i] != maxv:
                continue

            if y[n][i] != 1:
                print "result not correct: y is %s, y2 is %s" % (y[n], y2[n])
                print "patch name is %s" % verifydataset[n]
                break
            else:
                print "result correct: y is %s, y2 is %s" % (y[n], y2[n])
                print "patch name is %s" % verifydataset[n]
                break

    savedata('/root/ml-patch/data.pkl', [strlist ,opt.x])

def splitpatch(emailfile):
    data = loaddata('/root/ml-patch/data.pkl')
    strlist = data[0]
    theta = data[1]
    maildict = parsemail(emailfile)
    xlist = []
    patchsethead = {}
    result = {}

    for n in maildict.keys():
        tmparray = []
        subpatch=[]
        tmplist = getinfo(maildict[n], subpatch=subpatch)
        if subpatch == []:
            for i in strlist:
                if i in tmplist:
                    tmparray.append(1.0)
                else:
                    tmparray.append(0.0)
        else:
            tmplist = []
            patchsethead[n] = subpatch
            for m in subpatch:
                if m not in maildict.keys():
                    print "not find %s" % m
                    continue
                tmplist.extend(getinfo(maildict[m]))
            for i in strlist:
                if i in tmplist:
                    tmparray.append(1.0)
                else:
                    tmparray.append(0.0)

        xlist.append(tmparray)

    x = numpy.array(xlist)
    x = x.T

    nn = NN(x.shape[0], int(math.sqrt(x.shape[0] + 3)), 3, lamda=0.001)
    y = nn.FPformin(x, theta).T
    print "try to split %d patches" % len(maildict)
    for n in range(len(y)):
        maxv = y[n].max()
        for i in range(len(y[n])):
            if y[n][i] != maxv:
                continue

            result[maildict.keys()[n]] = [y[n], i + 1]
            break

    print len(result)
    for n in result.keys():
        if n in patchsethead.keys():
            group1=0
            group2=0
            group3=0
            for i in patchsethead[n]:
                if result[i][1] == 3:
                    group3 += 1
                if result[i][1] == 2:
                    group2 += 1
                if result[i][1] == 1:
                    group1 += 1

            if group3 > group2 and group3 > group1:
                print "split it to group 3"
                print "patch name is %s" % n
                print ""
                continue
            if group2 > group3 and group2 > group1:
                print "split it to group 2"
                print "patch name is %s" % n
                print ""
                continue
            if group1 > group3 and group1 > group2:
                print "split it to group 1"
                print "patch name is %s" % n
                print ""
                continue

        print "matrix is %s, split it to group %d" % (result[n][0], result[n][1])
        print "patch name is %s" % n
        print ""

if __name__ == '__main__':
    if not os.access("/root/ml-patch/data.pkl", os.R_OK):
        traindata()
    emailfile = glob.glob('/root/libvirttestmail/*')
    splitpatch(emailfile)
