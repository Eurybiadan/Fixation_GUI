__author__ = 'Robert F Cooper'

import struct
import time
from random import randint
from threading import Timer

import serial
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

    def set_fixation_cursor(self, cursor, start=0):
        return self.LCCanvas.set_fixation_cursor(cursor, start)

    def get_fixation_cursor(self):
        return self.LCCanvas.get_fixation_cursor()

    def show_fixation(self, show):
        self.LCCanvas.set_visible(show)


class LightCrafterCanvas(wx.Window):

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=0, name='LCCanvas'):
        wx.Window.__init__(self, parent, id, pos, size, style, name)

        #stimulus
        self.i = 0
        self.c = 0
        self.j = 0
        self.count = 0

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

    def set_fixation_cursor(self, cursor, start=0):
        lastcursor = self._cursor
        self._cursor = cursor
        self.repaint(start)
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

    def repaint(self, start=0):
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
            # how long the lines will be
            bx = self._location.x - (self._fixsize * 5)
            by = self._location.y - (self._fixsize * 5)
            tx = self._location.x + (self._fixsize * 5)
            ty = self._location.y + (self._fixsize * 5)

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
            elif self._cursor is 4:
                dc.SetPen(wx.Pen("WHITE"))
                for xloc in range(0, self.thisSize.x, 50):
                    dc.DrawLine(xloc, 0, xloc, self.thisSize.y)
                for yloc in range(0, self.thisSize.y, 50):
                    dc.DrawLine(0, yloc, self.thisSize.x, yloc)
            # Small Cross -JG
            elif self._cursor is 5:
                self._pen.SetWidth(self._fixsize)
                dc.SetPen(self._pen)
                dc.DrawLine(bx, self._location.y, tx, self._location.y)
                dc.DrawLine(self._location.x, by, self._location.x, ty)

            # Heather Stimulus only selected if piece of code is uncommented in fixgui keyboardpress f4
            elif self._cursor is 6:
                self.sequence(dc, self._location.x, self._location.y, start)


        del dc  # need to get rid of the MemoryDC before Update() is called.
        self.Refresh(eraseBackground=False)
        self.Update()
        # s.enter(2, 1, self.repaint)
        # s.run(False)

    def sequence(self, dc, locationx, locationy, start):
        with serial.Serial() as ser:
            # 0: blue, 1: green, 2: red; color array
            colors = [wx.Colour(red=0, green=0, blue=225), wx.Colour(red=94, green=255, blue=0), wx.Colour(red=195, green=255, blue=0)]
            # can use this to make the colors in random order, will probably work better if we have more colors
            index = randint(0, 2)

            ser.baudrate = 9600
            ser.port = 'COM3'
            ser.open()

            Open = struct.pack('!B', 64)
            Close = struct.pack('!B', 65)

            print('Open')
            ser.write(Open)

            time.sleep(1)  # careful with this, adds to redraw timer time
            print('Close')
            ser.write(Close)

            if self.i == 0:
                if self.c == 0:
                    self._pen.SetColour(colors[0])
                    self._brush.SetColour(colors[0])
                    dc.SetPen(self._pen)
                    dc.SetBrush(self._brush)
                    self.c = 1
                    dc.DrawCircle(locationx, locationy, 200)
                    print(time.perf_counter())

            if self.i == 1:
                if self.c == 1:
                    self._pen.SetColour(colors[1])
                    self._brush.SetColour(colors[1])
                    dc.SetPen(self._pen)
                    dc.SetBrush(self._brush)
                    self.c = 2
                    dc.DrawCircle(locationx, locationy, 200)
                    print(time.perf_counter())

            if self.i == 2:
                if self.c == 2:
                    self._pen.SetColour(colors[2])
                    self._brush.SetColour(colors[2])
                    dc.SetPen(self._pen)
                    dc.SetBrush(self._brush)
                    self.c = 0
                    dc.DrawCircle(locationx, locationy, 200)
                    print(time.perf_counter())

            self.i = self.i + 1
            if self.i == 3:
                self.i = 0

            del dc  # need to get rid of the MemoryDC before Update() is called.
            self.Refresh(eraseBackground=False)
            self.Update()

            if start == 1:
                self.count = 0
            t = Timer(0.5, self.repaint)
            t.start()
            if self.count >= 5:
                t.cancel()
            self.count = self.count + 1


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
