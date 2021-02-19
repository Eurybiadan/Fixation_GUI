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

        horzsizer.Add(self.LCCanvas, proportion=0, flag=wx.EXPAND)

    def set_fixation_centerpoint(self, location):
        self.LCCanvas.set_fixation_centerpoint(location)

    def set_fixation_location(self, location):
        self.LCCanvas.set_fixation_location(location)

    def set_fixation_color(self, penColor, brushColor):
        self.LCCanvas.set_fixation_color(penColor, brushColor)

    def set_fixation_size(self, size):
        self.LCCanvas.set_fixation_size(size)

    def set_fixation_cursor(self, cursor):
        return self.LCCanvas.set_fixation_cursor(cursor)

    def get_fixation_cursor(self):
        return self.LCCanvas.get_fixation_cursor()

    def show_fixation(self, show):
        self.LCCanvas.set_visible(show)


class LightCrafterCanvas(wx.Window):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='LCCanvas'):
        wx.Window.__init__(self, parent, id, pos, size, style, name)

        self._cursor = 0
        self._fixsize = 5
        self._center = wx.Point2D(size[0] / 2, size[1] / 2)
        self._location = wx.Point2D(self._center.x, self._center.y)
        self._pen = wx.Pen(wx.GREEN, self._fixsize, wx.PENSTYLE_SOLID)
        self._brush = wx.Brush(wx.GREEN, wx.BRUSHSTYLE_SOLID)
        self.draw_target = True


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
        self._pen.SetColour(penColor)
        self._brush.SetColour(brushColor)
        self.repaint()

    def set_fixation_size(self, size):
        self._fixsize = size
        self.repaint()

    def set_fixation_cursor(self, cursor):
        lastcursor = self._cursor
        self._cursor = cursor
        self.repaint()
        return lastcursor

    def set_visible(self, is_visible):
        self.draw_target = is_visible
        self.repaint()

    def get_fixation_cursor(self):
        return self._cursor

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

        if self.draw_target:
            self._pen.SetWidth(1)
            dc.SetPen(self._pen)
            dc.SetBrush(self._brush)
            tlcx = self._location.x - (self._fixsize / 2)
            tlcy = self._location.y - (self._fixsize / 2)
            # Used for Small Cross -JG
            bx = self._location.x - (self._fixsize * 2)
            by = self._location.y - (self._fixsize * 2)
            tx = self._location.x + (self._fixsize * 2)
            ty = self._location.y + (self._fixsize * 2)

            # Draw the fixation shape
            if self._cursor is 0:
                self._pen.SetWidth(self._fixsize)
                dc.SetPen(self._pen)
                dc.DrawLine(0, self._location.y, self.thisSize.x, self._location.y)
                dc.DrawLine(self._location.x, 0, self._location.x, self.thisSize.y)
            elif self._cursor is 1:
                self._pen.SetWidth(self._fixsize/3)
                dc.SetPen(self._pen)
                dc.SetBrush(wx.Brush("BLACK"))
                dc.DrawRectangle(tlcx, tlcy, self._fixsize, self._fixsize)
            elif self._cursor is 2:
                dc.DrawRectangle(tlcx, tlcy, self._fixsize, self._fixsize)
            elif self._cursor is 3:
                dc.SetBrush(self._brush)
                dc.DrawCircle(self._location.x, self._location.y, floor(self._fixsize / 2))
            # Small Cross -JG
            elif self._cursor is 5:
                self._pen.SetWidth(self._fixsize/3)
                dc.SetPen(self._pen)
                dc.DrawLine(bx, self._location.y, tx, self._location.y)
                dc.DrawLine(self._location.x, by, self._location.x, ty)
            elif self._cursor is 4:
                dc.SetPen(wx.Pen("WHITE"))
                for xloc in range(0, self.thisSize.x, 50):
                    dc.DrawLine(xloc, 0, xloc, self.thisSize.y)
                for yloc in range(0, self.thisSize.y, 50):
                    dc.DrawLine(0, yloc, self.thisSize.x, yloc)

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
