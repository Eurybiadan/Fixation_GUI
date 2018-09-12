from multiprocessing import Queue
import subprocess
import sys, os, socket
import threading


class FixGUIServer:

    def __init__(self, dataQueue=None):
        thispath = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

        py3path = os.path.join(thispath, 'venv', 'Scripts', 'pythonw.exe')
        print('Launching the Fixation GUI.')

        self.mainGUI = subprocess.Popen([py3path, 'wxFixGUI.py'])

        # Spawn the pair of listener threads so we can detect changes in the comm Queues passed by Savior
        self.whisperer = QueueWhisperer(dataQueue)  # This will recieve a tuple of sizes
        self.whisperer.start()


    def run_fixation_app_server(self, name):
        pass


# This thread class generically listens to a queue, and passes what it receives to a specified socket.
class QueueWhisperer(threading.Thread):
    def __init__(self, queue):

        threading.Thread.__init__(self)

        self.queue = queue

        self.HOST = 'localhost'
        self.PORT = 1222

    def run(self):
        self.serversock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversock.connect((self.HOST, self.PORT))

        while True:
            try:
                qData = self.queue.get(timeout=10)  # This is expected to be a tuple, but handle it in case it's not.

                msg = ""
                for data in qData:
                    msg += str(data) + ";"

                msg = msg[:-1]

                self.serversock.sendall(msg)
            except Queue.Empty:
                self.serversock
                # return
            except RuntimeError:
                print("Lost connection to the image listener!")
                if self.mainGUI:
                    self.mainGUI.kill()
                return


if __name__ == '__main__':
    import time
    testQ = Queue()

    CYANIDE = -1
    VIDNUM = 0
    FOV = 1

    server = FixGUIServer(testQ)
    time.sleep(6)
    testQ.put((FOV, 1, 1))
    testQ.put((VIDNUM, '0000'))
    time.sleep(1)
    testQ.put((FOV, 1.25, 1.25))
    testQ.put((VIDNUM, '0010'))
    time.sleep(1)
    testQ.put((FOV, 1.5, 1.5))
    testQ.put((VIDNUM, '0050'))
    time.sleep(1)
    testQ.put((FOV, 1.75, 1.75))
    testQ.put((VIDNUM, '0100'))
    time.sleep(1)

    testQ.put((CYANIDE, "I'm never gonna dance again"))










