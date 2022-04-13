#!/usr/bin/env python
"""
eigerStreamServer.py takes the EIGER stream and deals it to 
other servers for decoding frames into various formats.

"""
import argparse
import os
import sys
import datetime
#import pid
import tempfile
import time
import zmq
import sys
import threading
import time
from random import randint, random


__author__ = "Jon Schuermann"
__date__ = "17/02/14"

def tprint(msg):
    """like print, but won't get newlines confused with multiple threads"""
    sys.stdout.write(msg + '\n')
    sys.stdout.flush()



class ServerTask(threading.Thread):
    """ServerTask"""
    def __init__(self, verbose = False):
        """
        create stream listener object
        """
        #self.__host__ = '164.54.212.216'# host ip for 1Gb network
        self.__host__ = '192.168.0.1' # host ip for 10Gb network
        self.__port__ = 9999 # tcp stream port
        self.__verbose__ = verbose # verbosity

        self.connect() # start stream
        threading.Thread.__init__ (self)

    def connect(self):
        """
        open ZMQ pull socket
        return receiver object
        """
        print("[INFO] MAKE SURE STREAM INTERFACE IS ACTIVATED")

        context = zmq.Context()
        receiver = context.socket(zmq.PULL)
        receiver.connect("tcp://{0}:{1}".format(self.__host__,self.__port__))
        
        backend = context.socket(zmq.PUB)
        backend.bind('inproc://backend')
        
        #self.__receiver__ = receiver
        #print "[OK] initialized stream receiver for host tcp://{0}:{1}".format(self.__host__,self.__port__)
        #return self.__receiver__
        
        from fileWriter import stream2cbf_jon2
        fw = stream2cbf_jon2.Stream2Cbf(context, verbosity)
        
        #threading.Thread.__init__ (self)

    def run(self):
        context = zmq.Context()
        #frontend = context.socket(zmq.ROUTER)
        frontend = context.socket(zmq.PULL)
        frontend.bind('tcp://*:5570')

        backend = context.socket(zmq.PUB)
        backend.bind('inproc://backend')

        workers = []
        for i in range(5):
            worker = ServerWorker(context)
            worker.start()
            workers.append(worker)

        zmq.proxy(frontend, backend)

        frontend.close()
        backend.close()
        context.term()

class ServerWorker(threading.Thread):
    """ServerWorker"""
    def __init__(self, context):
        threading.Thread.__init__ (self)
        self.context = context

    def run(self):
        worker = self.context.socket(zmq.SUB)
        worker.connect('inproc://backend')
        tprint('Worker started')
        while True:
            ident, msg = worker.recv_multipart()
            tprint('Worker received %s from %s' % (msg, ident))
            replies = randint(0,4)
            for i in range(replies):
                time.sleep(1. / (randint(1,10)))
                worker.send_multipart([ident, msg])

        worker.close()

def main():
    """main function"""
    server = ServerTask()
    server.start()
    for i in range(3):
        client = ClientTask(i)
        client.start()

    server.join()

if __name__ == "__main__":
    main()
