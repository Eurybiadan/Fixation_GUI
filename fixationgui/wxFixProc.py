import asyncore
import threading
from multiprocessing import Queue
import subprocess
import sys, os, socket, platform
import time
import datetime


class FixGUIServer:

    def __init__(self, sendQueue=None, recvQueue=None):
        thispath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        if platform.system() is 'Windows':
            py3path = os.path.join(thispath, 'venv', 'Scripts', 'pythonw.exe')
        else:
            py3path = os.path.join(thispath, 'venv', 'bin', 'python3')
        guipath = os.path.join(thispath,'fixationgui', 'wxFixGUI.py')
        print('Launching the Fixation GUI at '+ py3path)

        self.mainGUI = subprocess.Popen([py3path, guipath])
        time.sleep(2)
        # Spawn the pair of listener threads so we can detect changes in the comm Queues passed by Savior
        self.whisperer = QueueWhisperer(sendQueue, recvQueue)  # This will recieve a tuple of sizes
        #asyncore.loop()
        self.whispererThread = threading.Thread(target=asyncore.loop, kwargs={'timeout': 1})
        self.whispererThread.start()


    def run_fixation_app_server(self, name):
        pass


# This thread class generically listens to a queue, and passes what it receives to a specified socket.
class QueueWhisperer(asyncore.dispatcher):
    def __init__(self, sendQueue=None, recvQueue=None):

        asyncore.dispatcher.__init__(self)

        self._sendQueue = sendQueue
        self._recvQueue = recvQueue


        self.HOST = 'localhost'
        self.PORT = 1222

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.connect((self.HOST, self.PORT))
        self.prevTime = datetime.datetime.now()


    def writable(self):
        return self._sendQueue.qsize() > 0

    def handle_read(self):
        # reads things sent from gui to savior?
        recvmsg = self.recv(32).decode("utf-8")
        if recvmsg == "F4" or "(" in recvmsg:
            if recvmsg == "F4":  # to avoid unforseen issues with FOV switches
                if (datetime.datetime.now() - self.prevTime) < datetime.timedelta(seconds=1):
                    # t = threading.Timer(0.5, self.queueDelayed, args=recvmsg)  # this is a thread with a delay that will call the queueDelayed function
                    # t.start()  # this starts the thread
                    return  # return and let people hit F4 until at least a second has passed. This way there won't be any issues with F4 freaking out/lagging if the button is spammed. Just going to discard the F4 message and wait for the next
            print("read in fixproc")
            print("Recieved: " + recvmsg)
            self._recvQueue.put(recvmsg)
            self.prevTime = datetime.datetime.now()
            print(self.prevTime)

    # def queueDelayed(self, recvmsg):  # this is the function that adds the message to the queue after being delayed to prevent errors
    #     print("In queueDelayed")
    #     print("Recieved: " + recvmsg)
    #     self._recvQueue.put(recvmsg)
    #     self.prevTime = datetime.datetime.now()
    #     print(self.prevTime)

    def handle_write(self):
        # writes the stuff coming into the fixation gui from savior
        try:
            qData = self._sendQueue.get()  # This is expected to be a tuple, but handle it in case it's not.

            msg = ""
            for data in qData:
                msg += str(data) + ";"

            msg = msg[:-1]
            msg += "!" # Terminate our message with an exclaimation.

            self.send(msg)

        except RuntimeError:
            print("Lost connection to the image listener!")
            self.close()
            if self.mainGUI:
                self.mainGUI.kill()
            return


if __name__ == '__main__':

    testQ = Queue()
    recvQ = Queue()

    CYANIDE = -1
    VIDNUM = 0
    FOV = 1
    OPEN = 2
    CLOSE = 3

    server = FixGUIServer(testQ, recvQ)
    # time.sleep(30)
    print("Starting test packets...")
    # before planned
    # testQ.put((FOV, 1.00, 1.00))
    # testQ.put((VIDNUM, '0001'))
    # testQ.put((OPEN, 35))
    # time.sleep(1)
    # testQ.put((CLOSE, 35))
    # testQ.put((FOV, 2.00, 2.00))
    # testQ.put((VIDNUM, '0002'))
    # time.sleep(20)
    # # planned
    # testQ.put((FOV, 1.00, 1.00))
    # testQ.put((VIDNUM, '0003'))
    # time.sleep(10)
    # # middle of plan
    # testQ.put((FOV, 1.00, 1.00))
    # testQ.put((VIDNUM, '0004'))
    # time.sleep(10)
    # # planned
    # testQ.put((FOV, 1.25, 1.25))
    # testQ.put((VIDNUM, '0004'))
    # time.sleep(5)
    # testQ.put((FOV, 1.25, 1.25))
    # testQ.put((VIDNUM, '0005'))
    # time.sleep(5)
    # testQ.put((FOV, 1.5, 1.5))
    # testQ.put((VIDNUM, '0006'))
    # time.sleep(5)
    # # after planned
    # testQ.put((FOV, 1.5, 1.5))
    # testQ.put((VIDNUM, '0007'))
    # time.sleep(2)
    # testQ.put((FOV, 1.75, 1.75))
    # testQ.put((VIDNUM, '0008'))
    # time.sleep(2)
    # testQ.put((FOV, 2, 2))
    # testQ.put((VIDNUM, '0009'))
    # time.sleep(2)
    # testQ.put((FOV, 2, 2))
    # testQ.put((VIDNUM, '0010'))

    #testQ.put((CYANIDE, "I'm never gonna dance again"))










