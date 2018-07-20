__author__ = 'Robert F Cooper'

import wx
from math import floor

# Sets Up The Class For The Program And Creates The Window
class wxLightCrafterFrame(wx.Frame):

    def __init__(self,parent=None,pos=wx.DefaultPosition,size=wx.DefaultSize, id=wx.ID_ANY):
        wx.Frame.__init__(self,parent,id,'wxLightCrafterFrame',pos,size,style=wx.BORDER_NONE)

        numdisplays = wx.Display().GetCount()
        # The Lightcrafter should be the LAST display index. Or we'll have problems.
        displayLC = wx.Display(numdisplays-1)

        geometry = displayLC.GetGeometry()
        print 'Top Left' + str(geometry.GetTopLeft())
        self.SetPosition(geometry.GetTopLeft())
        self.SetSize(geometry.GetSize())

        self.LCCanvas = LightCrafterCanvas(parent=self,size=self.GetSize())

        horzsizer=wx.BoxSizer(wx.HORIZONTAL)

        horzsizer.Add(self.LCCanvas,proportion=0,flag=wx.ALIGN_CENTER|wx.EXPAND)
        
    def SetFixationCenter(self,location):
        self.LCCanvas.SetFixationCenter(location)

    def SetFixationLocation(self,location):
        self.LCCanvas.SetFixationLocation(location)

    def SetFixationColor(self, penColor, brushColor):
        self.LCCanvas.SetFixationColor(penColor, brushColor)

    def SetFixationSize(self, size):
        self.LCCanvas.SetFixationSize(size)

    def SetFixationCursor(self,cursor):
        self.LCCanvas.SetFixationCursor(cursor)

class LightCrafterCanvas(wx.Window):

    def __init__(self,parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='LCCanvas'):
        wx.Window.__init__(self,parent,id,pos,size,style,name)

        self._cursor=0
        self._center = wx.Point2D(size[0]/2,size[1]/2)
        self._location = self._center
        self._penColor = wx.Pen(wx.GREEN,1,wx.SOLID)
        self._brushColor = wx.Brush(wx.GREEN,wx.SOLID)
        self._fixsize = 5

        self.OnSize(None)

        wx.EVT_PAINT(self, self.OnPaint)
        wx.EVT_SIZE(self, self.OnSize)

    def SetFixationCenter(self,location):
        self._center = self._center+location
        self.SetFixationLocation(wx.Point2D(0,0))

    def SetFixationLocation(self,location):
        self._location = self._center+location
        self.Repaint()

    def SetFixationColor(self, penColor, brushColor):
        self._penColor   = penColor
        self._brushColor = brushColor        
        self.Repaint()

    def SetFixationSize(self, size):
        self._fixsize = size;
        self.Repaint()

    def SetFixationCursor(self,cursor):
        self._cursor = cursor
        self.Repaint()

    def OnPaint(self, event):
        dc = wx.BufferedPaintDC(self,self._Buffer)

    def OnSize(self, event):
        self.thisSize = self.GetClientSize()

        self._Buffer = wx.EmptyBitmap(*self.thisSize)
        self.Repaint()

    def Repaint(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)

        dc.SetBrush( wx.Brush("BLACK"))
        dc.DrawRectangle(0,0,*self.thisSize)
        
        dc.SetPen(self._penColor)
        tlcx = self._location.x-(self._fixsize/2)
        tlcy = self._location.y-(self._fixsize/2)
            
        # Draw the fixation shape
        if self._cursor is 0:            
            dc.CrossHair(self._location.x,self._location.y)            
        elif self._cursor is 1:
            dc.SetBrush(self._brushColor)
            dc.DrawRectangle(tlcx,tlcy,self._fixsize,self._fixsize)
        elif self._cursor is 2:
            dc.DrawRectangle(tlcx,tlcy,self._fixsize,self._fixsize)
        elif self._cursor is 3:
            dc.SetBrush(self._brushColor)
            dc.DrawCircle(self._location.x,self._location.y, floor(self._fixsize/2))
            
        del dc # need to get rid of the MemoryDC before Update() is called.
        self.Refresh(eraseBackground=False)
        self.Update()

#Shows The Window
if __name__=='__main__':
    app=wx.App(redirect=False)

    numdisplays = wx.Display().GetCount()
    # The Lightcrafter should be the LAST display index. Or we'll have problems.
    displayLC = wx.Display(numdisplays-1)

    geometry = displayLC.GetGeometry()
    print 'Top Left' + str(geometry.GetTopLeft())
    frame=wxLightCrafterFrame(pos=geometry.GetTopLeft(),size=geometry.GetSize())

    frame.Show()
    app.MainLoop()
