__author__ = 'Robert F Cooper'

import random
import struct
import time
from threading import Timer

import serial
import wx
from math import floor
import datetime


# Sets Up The Class For The Program And Creates The Window
class wxLightCrafterFrame(wx.Frame):

    def __init__(self, parent=None, pos=wx.DefaultPosition, size=wx.DefaultSize, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, 'wxLightCrafterFrame', pos, size, style=wx.BORDER_NONE)

        numdisplays = wx.Display().GetCount()
        # The Lightcrafter should be the LAST display index. Or we'll have problems.
        displayLC = wx.Display(numdisplays - 1)
        # displayLC = wx.Display(numdisplays-2)  # Comment out for AO computers, only use for Jenna's desktop

        geometry = displayLC.GetGeometry()
        # print 'Top Left' + str(geometry.GetTopLeft())
        self.SetPosition(geometry.GetTopLeft())
        self.SetSize(geometry.GetSize())

        self.LCCanvas = LightCrafterCanvas(parent=self, size=self.GetSize())

        horzsizer = wx.BoxSizer(wx.HORIZONTAL)

        horzsizer.Add(self.LCCanvas, proportion=0, flag=wx.EXPAND)

    def set_fixation_centerpoint(self, location):
        self.LCCanvas.set_fixation_centerpoint(location)

    def set_fixation_location(self, location, MEAO=0):
        self.LCCanvas.set_fixation_location(location, MEAO)

    def set_fixation_color(self, penColor, brushColor):
        self.LCCanvas.set_fixation_color(penColor, brushColor)

    def set_fixation_size(self, size):
        self.LCCanvas.set_fixation_size(size)

    def set_fixation_cursor(self, cursor, start=0, port=100, wavelength=550, frequency=10, stimulusDuration=1):
        return self.LCCanvas.set_fixation_cursor(cursor, start, port, wavelength, frequency, stimulusDuration)

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
        self._stimpen = wx.Pen(wx.GREEN, self._fixsize, wx.PENSTYLE_SOLID)
        self._stimbrush = wx.Brush(wx.GREEN, wx.BRUSHSTYLE_SOLID)
        self.draw_target = True
        # self.draw_target = False  #changed to be off by default JG 10/19/2021


        self.on_size(None)

        wx.EvtHandler.Bind(self, wx.EVT_PAINT, self.on_paint)
        wx.EvtHandler.Bind(self, wx.EVT_SIZE, self.on_size)

    def set_fixation_centerpoint(self, location):
        self._center.x = self._center.x - location.x
        self._center.y = self._center.y + location.y
        self.set_fixation_location(wx.Point2D(0, 0))

    def set_fixation_location(self, location, MEAO = 0):
        # if MEAO is 1 that means we are using Rob's system at Marquette so the cross hair location has to be rotated
        # 90 degrees CCW so that it is still true with the gui
        if MEAO == 1:
            self._location.x = self._center.x + location.y
            self._location.y = self._center.y - location.x
        else:
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

    def set_fixation_cursor(self, cursor, start=0, port=100, wavelength=500, frequency=10, stimulusDuration=1):
        lastcursor = self._cursor
        self._cursor = cursor
        self.repaint(start, port, wavelength, frequency, stimulusDuration)
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

    def repaint(self, start=0, port=100, wavelength=500, frequency=10, stimulusDuration=1):
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
                dc.DrawLine(0, int(self._location.y), int(self.thisSize.x), int(self._location.y))
                dc.DrawLine(int(self._location.x), 0, int(self._location.x), int(self.thisSize.y))
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
        if self._cursor is 6:
            if self.draw_target:

                # Draw the fixation shape
                self._pen.SetWidth(self._fixsize)
                dc.SetPen(self._pen)
                dc.SetBrush(self._brush)
                dc.DrawLine(0, self._location.y, self.thisSize.x, self._location.y)
                dc.DrawLine(self._location.x, 0, self._location.x, self.thisSize.y)

            self.flicker(dc, self.thisSize.x/2, self.thisSize.y/2, start, port)  # this line for drawing circle in center of screen
            # self.stimulus(dc, self._location.x, self._location.y, start, port)  # this line for drawing circle where fixation target located


            # Heather Stimulus only selected if piece of code is uncommented in fixgui keyboardpress f4
        elif self._cursor is 7:
            if self.draw_target:

                # Draw the fixation shape
                self._pen.SetWidth(self._fixsize)
                dc.SetPen(self._pen)
                dc.SetBrush(self._brush)
                dc.DrawLine(0, self._location.y, self.thisSize.x, self._location.y)
                dc.DrawLine(self._location.x, 0, self._location.x, self.thisSize.y)

            # Index 0: Original cone stimulus: 550 nm (163, 255, 0)
            # Index 1: Red cone peak spectral sensitivity: 560 nm (195, 255, 0)
            # Index 2: Green cone peak spectral sensitivity: 530 nm (94, 255, 0)
            # Index 3: Blue cone peak spectral sensitivity: 440 nm (0, 0, 255)
            # Index 4: 450 nm cone stimulus for ARVO: (0, 70, 255)
            # Wavelength to rgb values generated from: https://academo.org/demos/wavelength-to-colour-relationship/
            colors = [wx.Colour(red=163, green=255, blue=0), wx.Colour(red=195, green=255, blue=0),
                      wx.Colour(red=94, green=255, blue=0), wx.Colour(red=0, green=0, blue=225), wx.Colour(red=0, green=70, blue=225)]
            if wavelength == 560:
                color = colors[1]
            elif wavelength == 450:
                color = colors[4]
            elif wavelength == 530:
                color = colors[2]
            elif wavelength == 440:
                color = colors[3]
            else:
                color = colors[0]

            self._stimpen.SetColour(color)
            self._stimbrush.SetColour(color)
            dc.SetPen(self._stimpen)
            dc.SetBrush(self._stimbrush)
            # if self.draw_target:
            dc.DrawCircle(self.thisSize.x/2, self.thisSize.y/2, 30)  # this line for drawing circle in center of screen #75 was original number
            # dc.DrawCircle(self._location.x, self._location.y, 75)  # this line for drawing circle where fixation target located
            # else:
                # dc.DrawRectangle(0, 0, self.thisSize.x, self.thisSize.y)  # this makes the entire screen the wavelength
            # print('DrawCircle @', time.perf_counter())
            del dc  # need to get rid of the MemoryDC before Update() is called.
            self.Refresh(eraseBackground=False)
            self.Update()

            self.stimulus(port, frequency)
            self.set_fixation_cursor(0)
            return

        elif self._cursor is 8:  # animal stimulus - set to open shutter
            self.animal_stimulus(port, stimulusDuration)
            self.set_fixation_cursor(0)

        elif self._cursor is 9:  # animal stimulus - set to close shutter
            self.animal_stimulus_close(port)
            self.set_fixation_cursor(0)

        del dc  # need to get rid of the MemoryDC before Update() is called.
        self.Refresh(eraseBackground=False)
        self.Update()
        # s.enter(2, 1, self.repaint)
        # s.run(False)

    def flicker(self, dc, locationx, locationy, start, port):

        with serial.Serial() as ser:
            # test color array w/ arbitrary wavelengths that are easy to tell the difference between
            # colors = [wx.Colour(red=163, green=255, blue=0), wx.Colour(red=255, green=0, blue=0), wx.Colour(red=0, green=255, blue=0), wx.Colour(red=0, green=0, blue=225)]
            if start == 1:
                self.indexList = list(range(0, 4))
                random.shuffle(self.indexList)
                # print(self.indexList)
            # Index 0: Original cone stimulus: 550 nm (163, 255, 0)
            # Index 1: Red cone peak spectral sensitivity: 560 nm (195, 255, 0)
            # Index 2: Green cone peak spectral sensitivity: 530 nm (94, 255, 0)
            # Index 3: Blue cone peak spectral sensitivity: 440 nm (0, 0, 255)
            # Wavelength to rgb values generated from: https://academo.org/demos/wavelength-to-colour-relationship/
            colors = [wx.Colour(red=163, green=255, blue=0), wx.Colour(red=195, green=255, blue=0), wx.Colour(red=94, green=255, blue=0), wx.Colour(red=0, green=0, blue=225)]

            # set the com port to the number the user specified
            comPort = 'COM' + str(port)
            # print('comPort is: ', comPort)

            ser.baudrate = 9600
            ser.port = comPort
            ser.open()

            # messages to send to the driver
            # time.sleep(5)
            Open = struct.pack('!B', 64)
            Close = struct.pack('!B', 65)

            # adapted from javascript, most likely don't actually need self.i but I kept in in for now
            if self.i == 0:
                if self.c == 0:
                    self._stimpen.SetColour(colors[self.indexList[0]])
                    self._stimbrush.SetColour(colors[self.indexList[0]])
                    dc.SetPen(self._stimpen)
                    dc.SetBrush(self._stimbrush)
                    self.c = 1
                    if self.draw_target:
                        dc.DrawCircle(locationx, locationy, 75)
                    else:
                        dc.DrawRectangle(0, 0, self.thisSize.x, self.thisSize.y)

            if self.i == 1:
                if self.c == 1:
                    self._stimpen.SetColour(colors[self.indexList[1]])
                    self._stimbrush.SetColour(colors[self.indexList[1]])
                    dc.SetPen(self._stimpen)
                    dc.SetBrush(self._stimbrush)
                    self.c = 2
                    if self.draw_target:
                        dc.DrawCircle(locationx, locationy, 75)
                    else:
                        dc.DrawRectangle(0, 0, self.thisSize.x, self.thisSize.y)

            if self.i == 2:
                if self.c == 2:
                    self._stimpen.SetColour(colors[self.indexList[2]])
                    self._stimbrush.SetColour(colors[self.indexList[2]])
                    dc.SetPen(self._stimpen)
                    dc.SetBrush(self._stimbrush)
                    self.c = 3
                    if self.draw_target:
                        dc.DrawCircle(locationx, locationy, 75)
                    else:
                        dc.DrawRectangle(0, 0, self.thisSize.x, self.thisSize.y)

            if self.i == 3:
                if self.c == 3:
                    self._stimpen.SetColour(colors[self.indexList[3]])
                    self._stimbrush.SetColour(colors[self.indexList[3]])
                    dc.SetPen(self._stimpen)
                    dc.SetBrush(self._stimbrush)
                    self.c = 0
                    if self.draw_target:
                        dc.DrawCircle(locationx, locationy, 75)
                    else:
                        dc.DrawRectangle(0, 0, self.thisSize.x, self.thisSize.y)

            self.i = self.i + 1
            if self.i == 4:
                self.i = 0

            del dc  # need to get rid of the MemoryDC before Update() is called.
            self.Refresh(eraseBackground=False)
            self.Update()

            # sleep to make sure there the color is fully switched before opening
            time.sleep(0.01)
            print('Open stimulus @', datetime.datetime.now())
            ser.write(Open)

            # display the color through the open shutter for 1 second
            time.sleep(0.5)  # careful with this, adds to redraw timer time
            # print('Closed @', time.perf_counter())
            ser.write(Close)

            # reset the count if a new video is being taken
            if start == 1:
                self.count = 0
            # set and start the timer to call repaint. Send the port number through
            t = Timer(1.75, self.repaint, args=[0, port])
            t.start()
            # cancel the timer if done with the cycle; 1 cycle = going through all the wavelengths once
            if self.count >= 3:
                t.cancel()
                self.set_fixation_cursor(0)
            # keep track of how many times repaint has been called
            self.count = self.count + 1

    def stimulus(self, port, frequency=30):  # edited to just deal with clock- no drawing JG 4/20
        with serial.Serial() as ser:

            # default values
            # 40 iterations should make it 4 seconds long?
            iterations = 40
            openTime = 0.05
            closedTime = 0.05

            if frequency == 30:
                # 100 iterations should make it 3.3 seconds long?
                iterations = 100
                openTime = 0.01
                closedTime = 0.023

            # set the com port to the number the user specified
            comPort = 'COM' + str(port)
            # print('comPort is: ', comPort)

            ser.baudrate = 9600
            ser.port = comPort
            ser.open()

            # messages to send to the driver
            # time.sleep(5)
            print('open flicker @: ', datetime.datetime.now())
            Open = struct.pack('!B', 64)
            Close = struct.pack('!B', 65)

            i = 0
            for i in range(iterations):
                # print('Closed @', time.perf_counter())
                ser.write(Close)
                time.sleep(closedTime)
                #print('Open @', time.perf_counter())
                ser.write(Open)
                time.sleep(openTime)  # careful with this, adds to redraw timer time
                i = i + 1

            ser.close()

    def animal_stimulus(self, port, stimulusDuration):

        with serial.Serial() as ser:

            # set the com port to the number the user specified
            comPort = 'COM' + str(port)
            # print('comPort is: ', comPort)

            ser.baudrate = 9600
            ser.port = comPort
            ser.open()

            # messages to send to the driver
            Open = struct.pack('!B', 64)
            print('Open @', time.perf_counter())
            ser.write(Open)

            time.sleep(stimulusDuration)

            Close = struct.pack('!B', 65)
            print('Close @', time.perf_counter())
            ser.write(Close)
            ser.close()



    def animal_stimulus_close(self, port):

        with serial.Serial() as ser:

            # set the com port to the number the user specified
            comPort = 'COM' + str(port)
            # print('comPort is: ', comPort)

            ser.baudrate = 9600
            ser.port = comPort
            ser.open()

            # messages to send to the driver
            Close = struct.pack('!B', 65)

            # print('Close @', time.perf_counter())
            ser.write(Close)
            ser.close()


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
