
from multiprocessing import Process
from wxFixGUI import wxFixationFrame
import wx


def __init__(self):
        pass
        #super(wxFixationFrameProc, self).__init__()
        #self.parent = parent

def run(name):
    app=wx.App()
    frame=wxFixationFrame(None)
    frame.Show()
    app.MainLoop()


if __name__=='__main__':
    
    p = Process(target=run,args=('bob',))
    p.start()
    p.join()
