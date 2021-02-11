import asyncore
import threading
from multiprocessing import Queue
import subprocess
import sys, os, socket, platform
import time


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


    def writable(self):
        return self._sendQueue.qsize() > 0

    def handle_read(self):
        recvmsg = self.recv(32).decode("utf-8")
        #print("Recieved: " + recvmsg)
        self._recvQueue.put(recvmsg)

    def handle_write(self):
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

    CYANIDE = -1
    VIDNUM = 0
    FOV = 1

    server = FixGUIServer(testQ)
    time.sleep(10)
    print("Starting test packets...")
    testQ.put((FOV, 3, 3))
    testQ.put((VIDNUM, '0000'))
    time.sleep(15)
    testQ.put((FOV, 0.75, 0.75))
    testQ.put((VIDNUM, '0001'))
    # time.sleep(2)
    # testQ.put((FOV, 0.75, 0.75))
    # testQ.put((VIDNUM, '0001'))
    # time.sleep(2)
    # testQ.put((FOV, 1, 1))
    # testQ.put((VIDNUM, '0000'))
    # time.sleep(2)
    # testQ.put((FOV, 1.25, 1.25))
    # testQ.put((VIDNUM, '0010'))
    # time.sleep(2)
    # testQ.put((FOV, 1.5, 1.5))
    # testQ.put((VIDNUM, '0050'))
    # time.sleep(2)
    # testQ.put((FOV, 1.75, 1.75))
    # testQ.put((VIDNUM, '0100'))
    # time.sleep(2)
    # testQ.put((FOV, 2, 2))
    # testQ.put((VIDNUM, '0100'))
    # time.sleep(2)
    # testQ.put((FOV, 2.25, 2.25))
    # testQ.put((VIDNUM, '0100'))
    # time.sleep(2)

    #testQ.put((CYANIDE, "I'm never gonna dance again"))










