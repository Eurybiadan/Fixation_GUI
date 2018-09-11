__author__ = 'Robert F Cooper'

import wx
from math import floor


# Sets Up The Class For The Program And Creates The Window
class wxLightCrafterFrame(wx.Frame):

    def __init__(self, parent=None, pos=wx.DefaultPosition, size=wx.DefaultSize, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, 'wxLightCrafterFrame', pos, size, style=wx.BORDER_NONE)

        numdisplays = wx.Display().GetCount()
        # The Lightcrafter should be the LAST display index. Or we'll have problems.
        displayLC = wx.Display(numdisplays - 1)

        geometry = displayLC.GetGeometry()
        # print 'Top Left' + str(geometry.GetTopLeft())
        self.SetPosition(geometry.GetTopLeft())
        self.SetSize(geometry.GetSize())

        self.LCCanvas = LightCrafterCanvas(parent=self, size=self.GetSize())

        horzsizer = wx.BoxSizer(wx.HORIZONTAL)

        horzsizer.Add(self.LCCanvas, proportion=0, flag=wx.ALIGN_CENTER | wx.EXPAND)

    def set_fixation_centerpoint(self, location):
        self.LCCanvas.set_fixation_centerpoint(location)

    def set_fixation_location(self, location):
        self.LCCanvas.set_fixation_location(location)

    def set_fixation_color(self, penColor, brushColor):
        self.LCCanvas.set_fixation_color(penColor, brushColor)

    def set_fixation_size(self, size):
        self.LCCanvas.set_fixation_size(size)

    def set_fixation_cursor(self, cursor):
        self.LCCanvas.set_fixation_cursor(cursor)


class LightCrafterCanvas(wx.Window):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='LCCanvas'):
        wx.Window.__init__(self, parent, id, pos, size, style, name)

        self._cursor = 0
        self._center = wx.Point2D(size[0] / 2, size[1] / 2)
        self._location = wx.Point2D(self._center.x, self._center.y)
        self._penColor = wx.Pen(wx.GREEN, 3, wx.PENSTYLE_SOLID)
        self._brushColor = wx.Brush(wx.GREEN, wx.BRUSHSTYLE_SOLID)

        self._fixsize = 5

        self.on_size(None)

        wx.EvtHandler.Bind(self, wx.EVT_PAINT, self.on_paint)
        wx.EvtHandler.Bind(self, wx.EVT_SIZE, self.on_size)

    def set_fixation_centerpoint(self, location):
        self._center.x = self._center.x - location.x
        self._center.y = self._center.y + location.y
        self.set_fixation_location(wx.Point2D(0, 0))

    def set_fixation_location(self, location):
        self._location.x = self._center.x - location.x
        self._location.y = self._center.y + location.y
        self.repaint()

    def set_fixation_color(self, penColor, brushColor):
        self._penColor = penColor
        self._brushColor = brushColor
        self.repaint()

    def set_fixation_size(self, size):
        self._fixsize = size;
        self.repaint()

    def set_fixation_cursor(self, cursor):
        self._cursor = cursor
        self.repaint()

    def on_paint(self, event):
        dc = wx.BufferedPaintDC(self, self._Buffer)

    def on_size(self, event):
        self.thisSize = self.GetClientSize()

        self._Buffer = wx.Bitmap(*self.thisSize)
        self.repaint()

    def repaint(self):
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)

        dc.SetBrush(wx.Brush("BLACK"))
        dc.DrawRectangle(0, 0, *self.thisSize)

        dc.SetPen(self._penColor)
        dc.SetBrush(self._brushColor)
        tlcx = self._location.x - (self._fixsize / 2)
        tlcy = self._location.y - (self._fixsize / 2)

        # Draw the fixation shape
        if self._cursor is 0:
            dc.DrawLine(0, self._location.y, self.thisSize.x, self._location.y)
            dc.DrawLine(self._location.x, 0, self._location.x, self.thisSize.y)
        elif self._cursor is 1:
            dc.SetBrush(self._brushColor)
            dc.DrawRectangle(tlcx, tlcy, self._fixsize, self._fixsize)
        elif self._cursor is 2:
            dc.DrawRectangle(tlcx, tlcy, self._fixsize, self._fixsize)
        elif self._cursor is 3:
            dc.SetBrush(self._brushColor)
            dc.DrawCircle(self._location.x, self._location.y, floor(self._fixsize / 2))

        del dc  # need to get rid of the MemoryDC before Update() is called.
        self.Refresh(eraseBackground=False)
        self.Update()


# Shows The Window
if __name__ == '__main__':
    app = wx.App(redirect=False)

    numdisplays = wx.Display().GetCount()
    # The Lightcrafter should be the LAST display index. Or we'll have problems.
    displayLC = wx.Display(numdisplays - 1)

    geometry = displayLC.GetGeometry()
    # print 'Top Left' + str(geometry.GetTopLeft())
    frame = wxLightCrafterFrame(pos=geometry.GetTopLeft(), size=geometry.GetSize())

    frame.Show()
    app.MainLoop()
