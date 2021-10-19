'''
Created on Sep 20, 2013

@author: Robert F Cooper
'''

import wx
from array import array
from LocSpin import LocSpin
import wx.lib.agw.floatspin as FS
from ViewPane import ViewPane
import numpy
import cv2
import os





class CursorPanel(wx.Panel):
    '''
    This class encapsulates the cursor modifying behavior of the Fixation GUI software.
    '''

    def __init__(self, parent, rootparent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.SIMPLE_BORDER, name='Cursor Control'):

        '''
        Constructor
        '''
        super(CursorPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour('black')
        self._rootparent = rootparent

        #print('in paneWid Cursor Panel')

        labelFont = wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)

        # Create the sizer for the miniPanel
        minipanesizer = wx.BoxSizer(wx.VERTICAL)

        widgetLabel = wx.StaticText(self, wx.ID_ANY, self.GetName())
        widgetLabel.SetForegroundColour('white')
        widgetLabel.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False))

        minipanesizer.Add(widgetLabel, 0, wx.ALIGN_CENTER)

        # Create pens for this class
        self.BLKPEN = wx.Pen(wx.BLACK, 3, wx.PENSTYLE_SOLID)
        self.WHITEPEN = wx.Pen(wx.WHITE, 3, wx.PENSTYLE_SOLID)
        self.MAGPEN = wx.Pen(wx.Colour(255, 0, 255), 3, wx.PENSTYLE_SOLID)
        self.REDPEN = wx.Pen(wx.RED, 3, wx.PENSTYLE_SOLID)
        self.GRNPEN = wx.Pen(wx.Colour(0, 255, 0, 255), 3, wx.PENSTYLE_SOLID)
        self.BLUPEN = wx.Pen(wx.BLUE, 3, wx.PENSTYLE_SOLID)
        self.YLWPEN = wx.Pen('Yellow', 3, wx.PENSTYLE_SOLID)
        self.GRAYPEN = wx.Pen(wx.Colour(75, 75, 75, 255), 3, wx.PENSTYLE_SOLID)

        # Create brushes for this class
        self.WHTBRSH_TRANS = wx.Brush(wx.WHITE, wx.TRANSPARENT)
        self.MAGENTABRSH = wx.Brush(wx.Colour(255, 0, 255), wx.BRUSHSTYLE_SOLID)
        self.REDBRSH = wx.Brush(wx.RED, wx.BRUSHSTYLE_SOLID)
        self.GREENBRSH = wx.Brush(wx.Colour(0, 255, 0, 255), wx.BRUSHSTYLE_SOLID)
        self.BLUEBRSH = wx.Brush(wx.BLUE, wx.BRUSHSTYLE_SOLID)
        self.YELLOWBRSH = wx.Brush('Yellow', wx.BRUSHSTYLE_SOLID)
        self.WHITEBRSH = wx.Brush(wx.WHITE, wx.BRUSHSTYLE_SOLID)
        self.GRAYBRSH = wx.Brush(wx.Colour(75, 75, 75, 255), wx.BRUSHSTYLE_SOLID)

        # Constants for transmission to the Arduino
        self.ARDMAG = 63519
        self.ARDRED = 7
        self.ARDYLW = 65504
        self.ARDGRN = 2016
        self.ARDBLU = 2047
        self.ARDWHT = 65535

        self.CROSS = 0
        self.SQOPEN = 1
        self.SQCLOSE = 2
        self.CIRCLE = 3
        self.SCROSS = 5
        # self.STIMULUS = 6

        self._iconsize = 25
        self._current_pen = self.GRNPEN
        self._current_brush = self.GREENBRSH

        # Make the cursor types for each button.

        # Cross (Serial command: 6,3)
        self._cross = wx.Bitmap(self._iconsize, self._iconsize)
        crosspoints = [(12, 2, 12, 23), (2, 12, 23, 12)]
        dc = wx.MemoryDC()
        dc.SelectObject(self._cross)
        dc.SetPen(self._current_pen)
        dc.SetBrush(self.WHTBRSH_TRANS)
        dc.DrawLineList(crosspoints)

        self._crossButton = wx.BitmapButton(self, wx.ID_ANY, self._cross, style=wx.BU_AUTODRAW, name='Cross')

        # Default is the cross button.
        self._cursorpressed = self._crossButton

        # Small Cross -JG
        self._scross = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._scross)
        dc.SetPen(self.GRAYPEN)
        dc.SetBrush(self.WHTBRSH_TRANS)
        dc.DrawLine(7, 12, 17, 12)
        dc.DrawLine(12, 7, 12, 17)

        self._scrossButton = wx.BitmapButton(self, wx.ID_ANY, self._scross, style=wx.BU_AUTODRAW, name='Small Cross')

        # Open Square (Serial command: 6,1,1)
        self._osquare = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._osquare)
        dc.SetPen(self.GRAYPEN)
        dc.DrawRectangle(4, 4, 17, 17)

        self._osquareButton = wx.BitmapButton(self, wx.ID_ANY, self._osquare, style=wx.BU_AUTODRAW, name='Open Square')

        # Closed Square (Serial command: 6,0,1)

        self._csquare = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._csquare)
        dc.SetBrush(self.GRAYBRSH)
        dc.DrawRectangle(4, 4, 17, 17)

        self._csquareButton = wx.BitmapButton(self, wx.ID_ANY, self._csquare, style=wx.BU_AUTODRAW,
                                              name='Closed Square')

        # Closed Circle (Serial command: 6,2,1)
        self._circle = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._circle)
        dc.SetBrush(self.GRAYBRSH)
        dc.DrawCircle(12, 12, 9)

        self._circleButton = wx.BitmapButton(self, wx.ID_ANY, self._circle, style=wx.BU_AUTODRAW, name='Circle')

        # This button stuff have been left in just in case we want another different fixation target - it can be changed to easily be that
        # Heather Stimulus
        # self._stim = wx.Bitmap(self._iconsize, self._iconsize)
        # dc.SelectObject(self._stim)
        # dc.SetBrush(self.GRAYBRSH)
        # dc.DrawCircle(12, 12, 9)
        #
        # self._stimButton = wx.BitmapButton(self, wx.ID_ANY, self._stim, style=wx.BU_AUTODRAW, name='Stimulus')

        del dc

        self._crossButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._scrossButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._osquareButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._csquareButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._circleButton.Bind(wx.EVT_BUTTON, self.OnButton)
        # self._stimButton.Bind(wx.EVT_BUTTON, self.OnButton)

        cursorsizer = wx.BoxSizer(wx.HORIZONTAL)

        cursorsizer.Add(self._crossButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._scrossButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._osquareButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._csquareButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._circleButton, 0, wx.ALL, 2)
        # cursorsizer.Add(self._stimButton, 0, wx.ALL, 2)

        self.buttonList = []

        # Magenta
        magentaico = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 0, 255, 255)
        magentaicodown = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 0, 255, 255)
        magButton = wx.BitmapButton(self, wx.ID_ANY, magentaico, style=wx.BU_AUTODRAW, name='Magenta')
        magButton.SetBitmapDisabled(magentaicodown)
        self.buttonList.append(magButton)
        # Red
        redico = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 0, 0, 255)
        redicodown = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 0, 0, 255)
        redButton = wx.BitmapButton(self, wx.ID_ANY, redico, style=wx.BU_AUTODRAW, name='Red')
        redButton.SetBitmapDisabled(redicodown)
        self.buttonList.append(redButton)
        # Yellow
        yellowico = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 255, 0, 255)
        yellowicodown = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 255, 0, 255)
        yelButton = wx.BitmapButton(self, wx.ID_ANY, yellowico, style=wx.BU_AUTODRAW, name='Yellow')
        yelButton.SetBitmapDisabled(yellowicodown)
        self.buttonList.append(yelButton)
        # Green
        greenico = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 0, 255, 0, 255)
        greenicodown = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 0, 255, 0, 255)
        grnButton = wx.BitmapButton(self, wx.ID_ANY, greenico, style=wx.BU_AUTODRAW, name='Green')
        grnButton.SetBitmapDisabled(greenicodown)
        self.buttonList.append(grnButton)
        # Blue
        blueico = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 0, 0, 255, 255)
        blueicodown = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 0, 0, 255, 255)
        bluButton = wx.BitmapButton(self, wx.ID_ANY, blueico, style=wx.BU_AUTODRAW, name='Blue')
        bluButton.SetBitmapDisabled(blueicodown)
        self.buttonList.append(bluButton)
        # White
        whiteico = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 255, 255, 255)
        whiteicodown = wx.Bitmap.FromRGBA(self._iconsize, self._iconsize, 255, 255, 255, 255)

        whtButton = wx.BitmapButton(self, wx.ID_ANY, whiteico, style=wx.BU_AUTODRAW, name='White')
        whtButton.SetBitmapDisabled(whiteicodown)
        self.buttonList.append(whtButton)

        # Add each button to the sizer, with a 2 pixel border around each.
        colorsizer = wx.BoxSizer(wx.HORIZONTAL)
        for button in self.buttonList:
            colorsizer.Add(button, 0, wx.ALL, 2)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)
        # Crosshair sizer default is 5, can change
        sizelabel = wx.StaticText(self, id=wx.ID_ANY, label='Cursor Size:')
        sizelabel.SetForegroundColour('white')
        sizelabel.SetFont(labelFont)
        sizeslider = wx.Slider(self, value=5, minValue=1, maxValue=20, size=(-1, -1),
                               style=wx.SL_HORIZONTAL | wx.SL_LABELS | wx.SL_BOTTOM)
        sizeslider.SetForegroundColour('white')
        sizeslider.SetFont(labelFont)
        sizeslider.Bind(wx.EVT_SCROLL, self.OnSliderScroll)

        sizesizer = wx.BoxSizer(wx.HORIZONTAL)
        sizesizer.Add(sizelabel, wx.ALIGN_TOP, wx.RIGHT | wx.LEFT, 2)
        sizesizer.Add(sizeslider, wx.CENTER, wx.RIGHT | wx.LEFT, 2)

        minipanesizer.Add(colorsizer)
        minipanesizer.Add(cursorsizer, 1, wx.ALIGN_RIGHT)
        minipanesizer.Add(sizesizer, 1, wx.EXPAND)

        self.SetSizerAndFit(minipanesizer)

    def RedrawCursors(self):

        self._cross = wx.Bitmap(self._iconsize, self._iconsize)
        crosspoints = [(12, 2, 12, 23), (2, 12, 23, 12)]
        dc = wx.MemoryDC()
        dc.SelectObject(self._cross)
        if self._cursorpressed is self._crossButton:
            dc.SetPen(self._current_pen)
            dc.SetBrush(self.WHTBRSH_TRANS)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.WHTBRSH_TRANS)
        dc.DrawLineList(crosspoints)

        self._crossButton.SetBitmapLabel(self._cross)

        # Small Cross -JG
        self._scross = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._scross)
        if self._cursorpressed is self._scrossButton:
            dc.SetPen(self._current_pen)
            dc.SetBrush(self.WHTBRSH_TRANS)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.WHTBRSH_TRANS)
        dc.DrawLine(7, 12, 17, 12)
        dc.DrawLine(12, 7, 12, 17)

        self._scrossButton.SetBitmapLabel(self._scross)

        # Open Square
        self._osquare = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._osquare)
        if self._cursorpressed is self._osquareButton:
            dc.SetPen(self._current_pen)
        else:
            dc.SetPen(self.GRAYPEN)
        dc.DrawRectangle(4, 4, 17, 17)

        self._osquareButton.SetBitmapLabel(self._osquare)

        # Closed Square
        self._csquare = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._csquare)
        if self._cursorpressed is self._csquareButton:
            dc.SetBrush(self._current_brush)
            dc.SetPen(self._current_pen)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.GRAYBRSH)

        dc.DrawRectangle(4, 4, 17, 17)

        self._csquareButton.SetBitmapLabel(self._csquare)

        # Closed Circle
        self._circle = wx.Bitmap(self._iconsize, self._iconsize)
        dc.SelectObject(self._circle)
        if self._cursorpressed is self._circleButton:
            dc.SetBrush(self._current_brush)
            dc.SetPen(self._current_pen)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.GRAYBRSH)
        dc.DrawCircle(12, 12, 9)

        self._circleButton.SetBitmapLabel(self._circle)

        # left to be reused if we ever want a different fixation target shape
        # Stimulus for Heather
        # self._stim = wx.Bitmap(self._iconsize, self._iconsize)
        # dc.SelectObject(self._stim)
        # if self._cursorpressed is self._stimButton:
        #     dc.SetBrush(self._current_brush)
        #     dc.SetPen(self._current_pen)
        # else:
        #     dc.SetPen(self.GRAYPEN)
        #     dc.SetBrush(self.GRAYBRSH)
        # dc.DrawCircle(12, 12, 9)
        #
        # self._stimButton.SetBitmapLabel(self._stim)


        del dc

    def OnButton(self, evt):
        pressed = evt.GetEventObject()
        # Check if it was one of the colors
        for button in self.buttonList:
            if pressed is button:
                ##                print "You pressed "+button.GetName()+"!"
                if button.GetName() == "Magenta":  # Magenta is 63519
                    self._current_pen = self.MAGPEN
                    self._current_brush = self.MAGENTABRSH
                elif button.GetName() == "Red":  # Red is 63488
                    self._current_pen = self.REDPEN
                    self._current_brush = self.REDBRSH
                elif button.GetName() == "Yellow":  # Yellow is 65504
                    self._current_pen = self.YLWPEN
                    self._current_brush = self.YELLOWBRSH
                elif button.GetName() == "Green":  # Green is 2016
                    self._current_pen = self.GRNPEN
                    self._current_brush = self.GREENBRSH
                elif button.GetName() == "Blue":  # Blue is 2047
                    self._current_pen = self.BLUPEN
                    self._current_brush = self.BLUEBRSH
                elif button.GetName() == "White":  # White is 65535
                    self._current_pen = self.WHITEPEN
                    self._current_brush = self.WHITEBRSH

                self._rootparent.update_fixation_color(self._current_pen.GetColour(), self._current_brush.GetColour())
                break

        if pressed is self._crossButton:
            self._rootparent.update_fixation_cursor(self.CROSS)
            self._cursorpressed = self._crossButton
        elif pressed is self._scrossButton:
            self._rootparent.update_fixation_cursor(self.SCROSS)
            self._cursorpressed = self._scrossButton
        elif pressed is self._osquareButton:
            self._rootparent.update_fixation_cursor(self.SQOPEN)
            self._cursorpressed = self._osquareButton
        elif pressed is self._csquareButton:
            self._rootparent.update_fixation_cursor(self.SQCLOSE)
            self._cursorpressed = self._csquareButton
        elif pressed is self._circleButton:
            self._rootparent.update_fixation_cursor(self.CIRCLE)
            self._cursorpressed = self._circleButton
        # elif pressed is self._stimButton:
        #     self._rootparent.update_fixation_cursor(self.STIMULUS)
        #     self._cursorpressed = self._stimButton

        self.RedrawCursors()

    def OnSliderScroll(self, evt):

        obj = evt.GetEventObject()
        val = obj.GetValue()
        self._rootparent.update_fixation_cursor_size(val)

# Added to set up all the buttons and usage for the planning panel -JG
class PlanningPanel(wx.Panel):

    def __init__(self, parent, rootparent, viewpaneref, fxguiself, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Reference Buttons Panel', port=None):
        super(PlanningPanel, self).__init__(parent, id, pos, size, style, name)
        self.imagespace = wx.Panel(parent, wx.ID_ANY)
        self.viewpaneref = viewpaneref
        self.fxguiself = fxguiself
        # default used for planning mode
        self.wxdata = 0

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        # label for FOV boxes area
        self.quicklabel = wx.StaticText(self, wx.ID_ANY, 'Field of View:', style=wx.ALIGN_CENTER)
        self.quicklabel.SetForegroundColour('white')
        self.quicklabel.SetFont(labelFont)

        # label for plan area
        self.quicklabel2 = wx.StaticText(self, wx.ID_ANY, 'Plan:', style=wx.ALIGN_CENTER)
        self.quicklabel2.SetForegroundColour('white')
        self.quicklabel2.SetFont(labelFont)

        self.buttonList = []
        self._rootparent = rootparent
        self.SetBackgroundColour('black')

        self.__deg_symbol = u'\N{DEGREE SIGN}'

        buttonsize = (60, 35)
        buttonalignment = wx.ALIGN_CENTER
        # FOV buttons - set up for AO 2.3 with FOV going from 0.5 to 2
        self.f05 = wx.Button(self, label='0.5x0.5', size=buttonsize)
        self.f05.SetBackgroundColour('medium gray')
        self.f05.SetForegroundColour('white')
        self.buttonList.append(self.f05)
        self.f075 = wx.Button(self, label='0.75x0.75', size=buttonsize)
        self.f075.SetBackgroundColour('medium gray')
        self.f075.SetForegroundColour('white')
        self.buttonList.append(self.f075)
        self.f1 = wx.Button(self, label='1.0x1.0', size=buttonsize)
        self.f1.SetBackgroundColour('medium gray')
        self.f1.SetForegroundColour('white')
        self.buttonList.append(self.f1)
        self.f125 = wx.Button(self, label='1.25x1.25', size=buttonsize)
        self.f125.SetBackgroundColour('medium gray')
        self.f125.SetForegroundColour('white')
        self.buttonList.append(self.f125)
        self.f14 = wx.Button(self, label='1.4x1.4', size=buttonsize)
        self.f14.SetBackgroundColour('medium gray')
        self.f14.SetForegroundColour('white')
        self.buttonList.append(self.f14)
        self.f15 = wx.Button(self, label='1.5x1.5', size=buttonsize)
        self.f15.SetBackgroundColour('medium gray')
        self.f15.SetForegroundColour('white')
        self.buttonList.append(self.f15)
        self.f175 = wx.Button(self, label='1.75x1.75', size=buttonsize)
        self.f175.SetBackgroundColour('medium gray')
        self.f175.SetForegroundColour('white')
        self.buttonList.append(self.f175)
        self.f2 = wx.Button(self, label='2.0x2.0', size=buttonsize)
        self.f2.SetBackgroundColour('medium gray')
        self.f2.SetForegroundColour('white')
        self.buttonList.append(self.f2)


        # Anchor cursor as center
        # mark button
        self.plan = wx.Button(self, label='Mark', size=(60, 35))
        self.plan.SetBackgroundColour('medium gray')
        self.plan.SetForegroundColour('white')
        self.buttonList.append(self.plan)

        # remove button
        self.remove = wx.Button(self, label='Remove', size=(60, 35))
        self.remove.SetBackgroundColour('medium gray')
        self.remove.SetForegroundColour('white')
        self.buttonList.append(self.remove)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer = wx.GridBagSizer()

        # positions for each of the FOV buttons and FOV label
        sizer.Add(self.quicklabel, (0, 0), (1, 4), buttonalignment)
        sizer.Add(self.f05, (1, 0), (1, 1), buttonalignment)
        sizer.Add(self.f075, (1, 1), (1, 1), buttonalignment)
        sizer.Add(self.f1, (1, 2), (1, 1), buttonalignment)
        sizer.Add(self.f125, (1, 3), (1, 1), buttonalignment)
        sizer.Add(self.f14, (2, 0), (1, 1), buttonalignment)
        sizer.Add(self.f15, (2, 1), (1, 1), buttonalignment)
        sizer.Add(self.f175, (2, 2), (1, 1), buttonalignment)
        sizer.Add(self.f2, (2, 3), (1, 1), buttonalignment)

        # positions for the plan and remove buttons and plan label
        sizer.Add(self.quicklabel2, (3, 0), (1, 4), buttonalignment)
        sizer.Add(self.plan, (4, 1), (1, 1), buttonalignment)
        sizer.Add(self.remove, (4, 2), (1, 1), buttonalignment)


        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)



    def OnButton(self, evt):
        pressed = evt.GetEventObject()

        # sends the fov to be set when the buttons are pressed
        if pressed is self.f05:
            fov = (0.5, 0.5)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f075:
            fov = (0.75, 0.75)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f1:
            fov = (1.0, 1.0)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f125:
            fov = (1.25, 1.25)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f14:
            fov = (1.4, 1.4)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f15:
            fov = (1.5, 1.5)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f175:
            fov = (1.75, 1.75)
            self.viewpaneref.set_fov(fov)
        if pressed is self.f2:
            fov = (2.0, 2.0)
            self.viewpaneref.set_fov(fov)

        if pressed is self.plan:
            # set remove mode to 0 since the button hit was plan, then set planmode to 1 because we are using plan mode, then send the info to mark location
            removemode = 0
            planmode = 1
            self.fxguiself.mark_location(self.wxdata, removemode, planmode)

        if pressed is self.remove:
            # set remove mode to 1 since the button hit was remove, then set planmode to 1 since we are using plan mode, then send the info to mark location
            removemode = 1
            planmode = 1
            self.fxguiself.mark_location(self.wxdata, removemode, planmode)


class ImInitPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, rootparent, viewpaneref, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Image Initialization Panel', port=None):
        wx.Panel.__init__(self, parent, id, pos, size, style, name)

        self.header_dir = ""
        self.filename = ""
        self.viewpaneref = viewpaneref
        self.buttonList = []
        self.SetBackgroundColour('black')
        self.tracker = 0
        self.ImageCoords = numpy.empty((0, 2), float)
        self.LiveCoords = numpy.empty((0, 2), float)
        self.recenter = 0
        self.rootparent = rootparent

        self.__deg_symbol = u'\N{DEGREE SIGN}'

        buttonalignment = wx.ALIGN_CENTER

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        self.quicklabel = wx.StaticText(self, wx.ID_ANY, 'Image Alignment:', style=wx.ALIGN_CENTER)
        self.quicklabel.SetForegroundColour('white')
        self.quicklabel.SetFont(labelFont)

        # AddImage
        self.AddImage = wx.Button(self, label='Load Background Image', size=(-1, 30))
        self.AddImage.SetBackgroundColour('medium gray')
        self.AddImage.SetForegroundColour('white')
        self.buttonList.append(self.AddImage)

        # Center Fovea
        self.CenterFovea = wx.Button(self, label='Center Fovea', size=(-1, 30))
        self.CenterFovea.SetBackgroundColour('medium gray')
        self.CenterFovea.SetForegroundColour('white')
        self.buttonList.append(self.CenterFovea)

        # Calibration & Select button
        # extra white space around words to make the button longer to fit the longer text later on once button is pressed
        self.Cali = wx.Button(self, label='            Start Image Calibration            ', size=(-1, 30))
        self.Cali.SetBackgroundColour('medium gray')
        self.Cali.SetForegroundColour('white')
        self.buttonList.append(self.Cali)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)
        sizer = wx.GridBagSizer()
        sizer.Add(self.quicklabel, (0, 0), (1, 3), buttonalignment)
        sizer.Add(self.AddImage, (1, 0), (1, 1), buttonalignment)
        sizer.Add(self.CenterFovea, (1, 1), (1, 3), buttonalignment)
        sizer.Add(self.Cali, (2, 0), (1, 4), buttonalignment)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

    def OnButton(self, evt):

        pressed = evt.GetEventObject()
        if pressed == self.AddImage:
            # call open background image
            self.on_open_background_image()
        if pressed == self.CenterFovea:
            height, width = self.img.shape[:2]
            # get the coordinates of the fovea in the image
            coordinates = self.viewpaneref._fixLoc
            # this is if this is the first time the fovea is being centered
            # if self.recenter == 0: # commented out because it didn't work -JG 10/14/21
            xdiff = 256.5 - coordinates.x
            ydiff = 256.5 - coordinates.y
            # need to save the old differences in case we need to recenter the fovea
            self.xdiffold = xdiff
            self.ydiffold = ydiff
            self.recenter = 1
            # this is if we are centering the fovea more than once # commented out because it didn't work -JG 10/14/21
            # else:
            #     xdiffnew = 256.5 - coordinates.x
            #     # add the differences together and save it to be the new old difference
            #     xdiff = self.xdiffold + xdiffnew
            #     self.xdiffold = xdiff
            #     ydiffnew = 256.5 - coordinates.y
            #     # add the differences together and save it to be the new old difference
            #     ydiff = self.ydiffold + ydiffnew
            #     self.ydiffold = ydiff

            T = numpy.float32([[1, 0, xdiff], [0, 1, ydiff]])
            # We use warpAffine to transform
            self.result = cv2.warpAffine(self.img, T, (width, height))
            # added this line in to make sure the calibrations start with the correct image if the fovea was already centered
            self.img = self.result

            # https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
            # save the transformed image temporarily
            self.filenamefov = 'tempimfovea.TIF'
            os.chdir(self.header_dir)
            cv2.imwrite(self.filenamefov, self.result)
            impath = self.header_dir + os.sep + self.filenamefov

            # https://wxpython.org/Phoenix/docs/html/wx.Image.html#wx.Image.LoadFile
            # Load in the file we just saved so we can make it a bitmap
            self.bkgrdim = wx.Bitmap(1, 1)
            self.bkgrdim.LoadFile(impath, wx.BITMAP_TYPE_ANY)

            # Update the image on the gui
            self.viewpaneref.set_bkgrd(self.bkgrdim)

            # delete the temporary file we made
            os.remove(self.filenamefov)

        if pressed == self.Cali:
            # if we are calibrating the image
            if self.tracker == 0:
                self.Cali.SetLabel('Select 1st Point on Live AO')
                self.tracker = self.tracker + 1
                # make sure the matrices are empty
                self.ImageCoords = numpy.empty((0, 2), float)
                self.LiveCoords = numpy.empty((0, 2), float)

            elif self.tracker == 1:
                # coordinates from 1st spot on image
                coordinates = self.viewpaneref._fixLoc
                self.ptli1 = numpy.float32(coordinates)
                # mark location on GUI
                self.viewpaneref.Repaint(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select Corresponding Point on Image')
                self.tracker = self.tracker + 1
                #here we need to tell it to stay in place
                self.rootparent.setFixStat()

            elif self.tracker == 2:
                # coordinates from 1st corresponding spot on live
                coordinates = self.viewpaneref._fixLoc
                self.ptim1 = numpy.float32(coordinates)
                # mark location on GUI
                self.viewpaneref.Repaint(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select 2nd Point on Live AO')
                self.tracker = self.tracker + 1
                self.rootparent.resetFixStat()

            elif self.tracker == 3:
                # coordinates from 2nd spot on image
                coordinates = self.viewpaneref._fixLoc
                self.ptli2 = numpy.float32(coordinates)
                # mark location on GUI
                self.viewpaneref.Repaint(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select Corresponding Point on Image')
                self.tracker = self.tracker + 1
                self.rootparent.setFixStat()

            elif self.tracker == 4:
                # coordinates from 2nd corresponding spot on live
                coordinates = self.viewpaneref._fixLoc
                self.ptim2 = numpy.float32(coordinates)
                # mark location on GUI
                self.viewpaneref.Repaint(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select 3rd Point on Live AO')
                self.tracker = self.tracker + 1
                self.rootparent.resetFixStat()

            elif self.tracker == 5:
                # coordinates from 3rd spot on image
                coordinates = self.viewpaneref._fixLoc
                self.ptli3 = numpy.float32(coordinates)
                # mark location on GUI
                self.viewpaneref.Repaint(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select Corresponding Point on Image')
                self.tracker = self.tracker + 1
                self.rootparent.setFixStat()

            elif self.tracker == 6:
                # coordinates from 3rd corresponding spot on live
                coordinates = self.viewpaneref._fixLoc
                self.ptim3 = numpy.float32(coordinates)
                # mark location on GUI
                self.viewpaneref.Repaint(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Calibrate')
                self.tracker = self.tracker + 1
                self.rootparent.resetFixStat()

            elif self.tracker == 7:
                # Putting all the coordinates together
                self.ptsim = numpy.float32([self.ptim1, self.ptim2, self.ptim3])
                self.ptsli = numpy.float32([self.ptli1, self.ptli2, self.ptli3])

                # The Affine Transformation
                self.matrix = cv2.getAffineTransform(self.ptsli, self.ptsim)
                self.result = cv2.warpAffine(self.img, self.matrix, (self.cols, self.rows))

                # https://www.geeksforgeeks.org/python-opencv-cv2-imwrite-method/
                # save the transformed image temporarily
                filename = 'tempim.TIF'
                os.chdir(self.header_dir)
                cv2.imwrite(filename, self.result)
                impath = self.header_dir + os.sep + filename

                # https://wxpython.org/Phoenix/docs/html/wx.Image.html#wx.Image.LoadFile
                # Load in the file we just saved so we can make it a bitmap
                self.bkgrdim = wx.Bitmap(1, 1)
                self.bkgrdim.LoadFile(impath, wx.BITMAP_TYPE_ANY)


                # reset the background to the new transformed image
                self.viewpaneref.clear_calicoords()
                self.viewpaneref.set_bkgrd(self.bkgrdim)

                # change button label
                self.Cali.SetLabel('New Calibration')
                self.tracker = 0

                # delete the temporary file we made
                os.remove(filename)

    def on_open_background_image(self, evt=None):
        dialog = wx.FileDialog(self, 'Select background image:', self.header_dir, self.filename,
                               'Image files (*.jpg,*.jpeg,*.bmp,*.png,*.tif,*.tiff)| *.jpg;*.jpeg;*.bmp;*.png;*.tif;*.tiff|' +
                               'JP(E)G images (*.jpg,*.jpeg)|*.jpg;*.jpeg|BMP images (*.bmp)|*.bmp' +
                               '|PNG images (*.png)|*.png|TIF(F) images (*.tif,*.tiff)|*.tif;*.tiff', wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.header_dir = dialog.GetDirectory()
            self.filename = dialog.GetFilename()
            dialog.Destroy()
            impath = self.header_dir + os.sep + self.filename

            self.bkgrdim = wx.Bitmap(1, 1)
            self.bkgrdim.LoadFile(impath, wx.BITMAP_TYPE_ANY)
            # JG need for transformations
            self.img = cv2.imread(impath)
            self.rows, self.cols, self.ch = self.img.shape

            # determining dimensions to resize the image based on current aspect ratio
            ratio = self.rows/self.cols
            # if the ratio is over 1, the height is greater than width so we need to make width at least 513 and then fit the height to keep aspect ratio
            if ratio > 1:
                width = 513
                self.cols = width
                height = int(ratio * width)
                self.rows = height
            # height should be at least 513 to fill the entire grid- - width will be larger but determined by the actual aspect ratio
            else:
                height = 513
                self.rows = height
                width = int(height/ratio)
                self.cols = width

            # Scale the bitmap
            image = wx.ImageFromBitmap(self.bkgrdim)
            image = image.Scale(width, height, wx.IMAGE_QUALITY_HIGH)
            self.bkgrdim = wx.BitmapFromImage(image)
            self.viewpaneref.set_bkgrd(self.bkgrdim)

            # scale the image
            self.img = cv2.resize(self.img, (width, height))

class AutoAdvance(wx.Panel):

    '''
    classdocs
    '''

    def __init__(self, parent, rootparent, protocolref, MessageEvent, myEVT_RETURN_MESSAGE, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Quick Locations Panel', port=None):
        super(AutoAdvance, self).__init__(parent, id, pos, size, style, name)

        self.protocolref = protocolref
        self.protocolref.i = 0
        self.count = 0
        self.firstTime = 0
        self.messageEvent = MessageEvent
        self.myEvtRetMsg = myEVT_RETURN_MESSAGE
        self.buttonList = []
        self._rootparent = rootparent
        self.SetBackgroundColour('black')

        self.__deg_symbol = u'\N{DEGREE SIGN}'

        buttonalignment = wx.ALIGN_CENTER

        # Auto Advance
        self.autoA = wx.Button(self, label='Advance', size=(-1, 30))
        self.autoA.SetBackgroundColour('medium gray')
        self.autoA.SetForegroundColour('white')
        self.buttonList.append(self.autoA)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer = wx.GridBagSizer()
        sizer.Add(self.autoA, (0, 0), (1, 0), buttonalignment)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

        protocolref.loadMessageEvtObjects(self.messageEvent, self.myEvtRetMsg)

    def OnButton(self, evt):
        self.protocolref.i = self.protocolref.list.GetItemCount() - self.protocolref.plannedList + self.count
        # if we aren't in load planed mode button has no functionality
        if self.protocolref.loadplanmode == 0:
            return
        ind = self.protocolref.list.GetItemCount()
        pressed = evt.GetEventObject()
        if pressed == self.autoA:
            # check to make sure the index won't go out of bounds
            if self.protocolref.i >= ind:
                return
            item = self.protocolref._plannedProtocol[self.count]
            self.protocolref.on_listitem_selected(0, item, self.protocolref.i)
            # sets the current auto advance selected color
            self.protocolref.list.SetItemBackgroundColour(self.protocolref.i, (74, 0, 0))
            # setting the list item colors after the auto advance has passed
            if self.count > (self.protocolref.list.GetItemCount() - self.protocolref.plannedList):
                # get the previous item on the list
                previtem = self.protocolref._plannedProtocol[self.count - 1]
                # if imaged there, set color to black, else set back to loaded in blue color
                if int(previtem['videoNumber']) >= 0:
                    self.protocolref.list.SetItemBackgroundColour(self.protocolref.i-1, (0, 0, 0))
                else:
                    self.protocolref.list.SetItemBackgroundColour(self.protocolref.i-1, (0, 102, 102))
            self.count = self.count + 1



class RefButtonsPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, rootparent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Reference Buttons Panel', port=None):
        super(RefButtonsPanel, self).__init__(parent, id, pos, size, style, name)

        self.buttonList = []
        self.oldref = None
        self.oldoffset = None
        self._rootparent = rootparent
        self.SetBackgroundColour('black')

        self.__deg_symbol = u'\N{DEGREE SIGN}'

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        buttonalignment = wx.ALIGN_CENTER

        # Anchor cursor as center
        self.setRef = wx.Button(self, label='Set Reference Point', size=(-1, 30))
        self.setRef.SetBackgroundColour('medium gray')
        self.setRef.SetForegroundColour('white')
        self.buttonList.append(self.setRef)

        self.reSet = wx.Button(self, label='Reset Reference Point to (0,0)', size=(-1, 30))
        self.reSet.SetBackgroundColour('medium gray')
        self.reSet.SetForegroundColour('white')
        self.buttonList.append(self.reSet)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer = wx.GridBagSizer()
        sizer.Add(self.setRef, (0, 0), (1, 3), buttonalignment)
        sizer.Add(self.reSet, (1, 0), (1, 3), buttonalignment)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

    def OnButton(self, evt):
        pressed = evt.GetEventObject()

        if pressed is self.setRef:
            dlg = wx.MessageDialog(self._rootparent, "Are you sure you want to set a new reference point?", "Are you sure?", wx.YES_NO | wx.ICON_QUESTION)

            res = dlg.ShowModal()
            if res == wx.ID_YES:
                tmp = self._rootparent.degrees_to_screenpix(self._rootparent.horz_loc, self._rootparent.vert_loc)
                self.oldref = self._rootparent.degrees_to_screenpix(-self._rootparent.horz_loc, -self._rootparent.vert_loc)
                offset = wx.Point2D(tmp[0], tmp[1])
                self.oldoffset = wx.Point2D(self.oldref[0], self.oldref[1])
                self._rootparent.LCCanvas.set_fixation_centerpoint(offset)
                self._rootparent.update_fixation_location(wx.Point2D(0, 0))

        if pressed is self.reSet:
            dlg = wx.MessageDialog(self._rootparent,
                                       "Would you like to reset the reference point to (0,0)?", "Reset Reference Point?", wx.YES_NO | wx.ICON_QUESTION)
            res = dlg.ShowModal()
            if res == wx.ID_YES:
                if self.oldoffset != None:
                    self._rootparent.LCCanvas.set_fixation_centerpoint(self.oldoffset)
                    self._rootparent.update_fixation_location(wx.Point2D(0, 0))
                    self.oldoffset = None
            

class QuickLocationsPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, rootparent, protocolref, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Quick Locations Panel', port=None):
        super(QuickLocationsPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour('black')
        self._rootparent = rootparent
        self._protocolref = protocolref

        self.__deg_symbol = u'\N{DEGREE SIGN}'

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        self.quicklabel = wx.StaticText(self, wx.ID_ANY, 'Quick Locs:', style=wx.ALIGN_CENTER)
        self.quicklabel.SetForegroundColour('white')
        self.quicklabel.SetFont(labelFont)

        self.buttonList = []

        buttonsize = (35, 35)
        buttonalignment = wx.ALIGN_CENTER
        self.TLC = wx.Button(self, label='TLC', size=buttonsize)
        self.TLC.SetBackgroundColour('medium gray')
        self.TLC.SetForegroundColour('white')
        self.buttonList.append(self.TLC)
        self.MTE = wx.Button(self, label='MTE', size=buttonsize)
        self.MTE.SetBackgroundColour('medium gray')
        self.MTE.SetForegroundColour('white')
        self.buttonList.append(self.MTE)
        self.TRC = wx.Button(self, label='TRC', size=buttonsize)
        self.TRC.SetBackgroundColour('medium gray')
        self.TRC.SetForegroundColour('white')
        self.buttonList.append(self.TRC)
        self.MRE = wx.Button(self, label='MRE', size=buttonsize)
        self.MRE.SetBackgroundColour('medium gray')
        self.MRE.SetForegroundColour('white')
        self.buttonList.append(self.MRE)
        self.BRC = wx.Button(self, label='BRC', size=buttonsize)
        self.BRC.SetBackgroundColour('medium gray')
        self.BRC.SetForegroundColour('white')
        self.buttonList.append(self.BRC)
        self.MBE = wx.Button(self, label='MBE', size=buttonsize)
        self.MBE.SetBackgroundColour('medium gray')
        self.MBE.SetForegroundColour('white')
        self.buttonList.append(self.MBE)
        self.BLC = wx.Button(self, label='BLC', size=buttonsize)
        self.BLC.SetBackgroundColour('medium gray')
        self.BLC.SetForegroundColour('white')
        self.buttonList.append(self.BLC)
        self.MLE = wx.Button(self, label='MLE', size=buttonsize)
        self.MLE.SetBackgroundColour('medium gray')
        self.MLE.SetForegroundColour('white')
        self.buttonList.append(self.MLE)
        self.CTR = wx.Button(self, label='CTR', size=buttonsize)
        self.CTR.SetBackgroundColour('medium gray')
        self.CTR.SetForegroundColour('white')
        self.buttonList.append(self.CTR)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer = wx.GridBagSizer()
        sizer.Add(self.quicklabel, (0, 0), (1, 3), buttonalignment)
        sizer.Add(self.TLC, (1, 0), (1, 1), buttonalignment)
        sizer.Add(self.MTE, (1, 1), (1, 1), buttonalignment)
        sizer.Add(self.TRC, (1, 2), (1, 1), buttonalignment)
        sizer.Add(self.MLE, (2, 0), (1, 1), buttonalignment)
        sizer.Add(self.CTR, (2, 1), (1, 1), buttonalignment)
        sizer.Add(self.MRE, (2, 2), (1, 1), buttonalignment)
        sizer.Add(self.BLC, (3, 0), (1, 1), buttonalignment)
        sizer.Add(self.MBE, (3, 1), (1, 1), buttonalignment)
        sizer.Add(self.BRC, (3, 2), (1, 1), buttonalignment)

        box = wx.BoxSizer(wx.VERTICAL) # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

    def OnButton(self, evt):
        pressed = evt.GetEventObject()

        v_fov = self._rootparent.get_vertical_fov()
        h_fov = self._rootparent.get_horizontal_fov()

        for button in self.buttonList:
            if pressed is button:
                if button.GetLabelText() == 'TLC':
                    self._rootparent.update_fixation_location(wx.Point2D(-h_fov/2, v_fov/2))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'MTE':
                    self._rootparent.update_fixation_location(wx.Point2D(0, v_fov / 2))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'TRC':
                    self._rootparent.update_fixation_location(wx.Point2D(h_fov/2, v_fov/2))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'MRE':
                    self._rootparent.update_fixation_location(wx.Point2D(h_fov / 2, 0))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'BRC':
                    self._rootparent.update_fixation_location(wx.Point2D(h_fov/2, -v_fov/2))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'MBE':
                    self._rootparent.update_fixation_location(wx.Point2D(0, -v_fov/2))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'BLC':
                    self._rootparent.update_fixation_location(wx.Point2D(-h_fov/2, -v_fov/2))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'MLE':
                    self._rootparent.update_fixation_location(wx.Point2D(-h_fov/2, 0))
                    self._protocolref.quickLoc(button.GetLabelText())
                elif button.GetLabelText() == 'CTR':
                    self._rootparent.update_fixation_location(wx.Point2D(0, 0))
                    self._protocolref.quickLoc(button.GetLabelText())
