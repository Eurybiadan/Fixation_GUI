'''
Created on Sep 20, 2013

@author: Robert F Cooper
'''

import wx
from array import array


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

        self._iconsize = 25
        self._current_pen = self.GRNPEN
        self._current_bursh = self.GREENBRSH

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

        self._circleButton = wx.BitmapButton(self, wx.ID_ANY, self._circle, style=wx.BU_AUTODRAW, name='Square')

        del dc

        self._crossButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._osquareButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._csquareButton.Bind(wx.EVT_BUTTON, self.OnButton)
        self._circleButton.Bind(wx.EVT_BUTTON, self.OnButton)

        cursorsizer = wx.BoxSizer(wx.HORIZONTAL)

        cursorsizer.Add(self._crossButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._osquareButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._csquareButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._circleButton, 0, wx.ALL, 2)

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
            dc.SetBrush(self._current_bursh)
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
            dc.SetBrush(self._current_bursh)
            dc.SetPen(self._current_pen)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.GRAYBRSH)
        dc.DrawCircle(12, 12, 9)

        self._circleButton.SetBitmapLabel(self._circle)

        del dc

    def OnButton(self, evt):
        pressed = evt.GetEventObject()
        # Check if it was one of the colors
        for button in self.buttonList:
            if pressed is button:
                ##                print "You pressed "+button.GetName()+"!"
                if button.GetName() == "Magenta":  # Magenta is 63519
                    self._current_pen = self.MAGPEN
                    self._current_bursh = self.MAGENTABRSH
                elif button.GetName() == "Red":  # Red is 63488
                    self._current_pen = self.REDPEN
                    self._current_bursh = self.REDBRSH
                elif button.GetName() == "Yellow":  # Yellow is 65504
                    self._current_pen = self.YLWPEN
                    self._current_bursh = self.YELLOWBRSH
                elif button.GetName() == "Green":  # Green is 2016
                    self._current_pen = self.GRNPEN
                    self._current_bursh = self.GREENBRSH
                elif button.GetName() == "Blue":  # Blue is 2047
                    self._current_pen = self.BLUPEN
                    self._current_bursh = self.BLUEBRSH
                elif button.GetName() == "White":  # White is 65535
                    self._current_pen = self.WHITEPEN
                    self._current_bursh = self.WHITEBRSH

                self._rootparent.update_fixation_color(self._current_pen.GetColour(), self._current_bursh.GetColour())
                break

        if pressed is self._crossButton:
            self._rootparent.update_fixation_cursor(self.CROSS)
            self._cursorpressed = self._crossButton
        elif pressed is self._osquareButton:
            self._rootparent.update_fixation_cursor(self.SQOPEN)
            self._cursorpressed = self._osquareButton
        elif pressed is self._csquareButton:
            self._rootparent.update_fixation_cursor(self.SQCLOSE)
            self._cursorpressed = self._csquareButton
        elif pressed is self._circleButton:
            self._rootparent.update_fixation_cursor(self.CIRCLE)
            self._cursorpressed = self._circleButton

        self.RedrawCursors()

    def OnSliderScroll(self, evt):

        obj = evt.GetEventObject()
        val = obj.GetValue()
        self._rootparent.update_fixation_cursor_size(val)


class ImInitPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Image Initialization Panel', port=None):
        wx.Panel.__init__(self, parent, id, pos, size, style, name)

        self.SetBackgroundColour('black')

        self.__deg_symbol = u'\N{DEGREE SIGN}'
        self._slider_val = 0
        self._sliderObservers = []

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        # Select Image Button
        self.selectim = wx.Button(self, label='Select Image', size=(-1, 30))
        self.selectim.SetBackgroundColour('medium gray')
        self.selectim.SetForegroundColour('white')

        # Align ViewPane
        self.initalign = wx.Button(self, label='Initialization', size=(-1, 30))
        self.initalign.SetBackgroundColour('medium gray')
        self.initalign.SetForegroundColour('white')

        butsizer = wx.BoxSizer(wx.HORIZONTAL)
        butsizer.Add(self.selectim, 1, wx.ALIGN_CENTER | wx.ALL, 5)
        butsizer.Add(self.initalign, 1, wx.ALIGN_CENTER | wx.ALL, 5)

        # Rotation slider
        self.rotlabel = wx.StaticText(self, wx.ID_ANY, '0.0' + self.__deg_symbol)
        self.rotlabel.SetForegroundColour('white')
        self.rotlabel.SetFont(labelFont)
        self.rotlabel.Hide()
        self.rotslider = wx.Slider(self, wx.ID_ANY, value=0, minValue=-20, maxValue=20)
        self.rotslider.SetTickFreq(1)

        self.Bind(wx.EVT_SCROLL, self.OnRotationSlider)

        rotsizer = wx.BoxSizer(wx.HORIZONTAL)
        rotsizer.Add(self.rotslider, 0, wx.ALIGN_CENTER)
        rotsizer.Add(self.rotlabel, 0, wx.ALIGN_CENTER)

        panesizer = wx.BoxSizer(wx.VERTICAL)

        panesizer.Add(butsizer, 0, wx.ALIGN_CENTER)
        panesizer.Add(rotsizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(panesizer)
        self.rotslider.Hide()
        self.rotlabel.Hide()

    def SetState(self, state):

        if state == 0:
            self.rotslider.Hide()
            self.rotlabel.Hide()
            self.Layout()
            self.initalign.SetLabel("Initialization")
        elif state == 1:
            self.initalign.SetLabel("Pan/Zoom")
        elif state == 2:
            self.rotslider.Show()
            self.rotlabel.Show()
            self.Layout()
            self.initalign.SetLabel("Rotate/Zoom")

    def OnRotationSlider(self, event):
        if event.GetEventObject() is self.rotslider:
            self.SetRotationValue(event.GetPosition() / 2.0)
            self.rotlabel.SetLabel(str(self._slider_val) + self.__deg_symbol)

    def SetRotationValue(self, val):
        self._slider_val = val
        for callback in self._sliderObservers:
            callback(self._slider_val)

    def GetRotationValue(self):
        return self._slider_val

    def BindTo(self, callback):
        self._sliderObservers.append(callback)

class RefButtonsPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, rootparent,id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Reference Buttons Panel', port=None):
        super(RefButtonsPanel, self).__init__(parent, id, pos, size, style, name)

        self._rootparent = rootparent
        self.SetBackgroundColour('black')

        self.__deg_symbol = u'\N{DEGREE SIGN}'

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        # Anchor cursor as center
        self.anchorbut = wx.Button(self, label='Set Reference Point', size=(-1, 30))
        self.anchorbut.SetBackgroundColour('medium gray')
        self.anchorbut.SetForegroundColour('white')
        self.anchorbut.Bind(wx.EVT_BUTTON, self.OnButton)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(self.anchorbut, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

    def OnButton(self, evt):
        pressed = evt.GetEventObject()

        if pressed is self.anchorbut:
            dlg = wx.MessageDialog(self._rootparent, "Are you sure you want to set a new reference point? This process is irreversable.", "Are you sure?", wx.YES_NO | wx.ICON_QUESTION)

            res = dlg.ShowModal()
            if res == wx.ID_YES:
                tmp = self._rootparent.degrees_to_screenpix(self._rootparent.horz_loc, self._rootparent.vert_loc)
                offset = wx.Point2D(tmp[0], tmp[1])
                self._rootparent.LCCanvas.set_fixation_centerpoint(offset)
                self._rootparent.update_fixation_location(wx.Point2D(0, 0))

class QuickLocationsPanel(wx.Panel):
    '''
    classdocs
    '''

    def __init__(self, parent, rootparent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Quick Locations Panel', port=None):
        super(QuickLocationsPanel, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour('black')
        self._rootparent = rootparent

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
        self.MID = wx.Button(self, label='MID', size=buttonsize)
        self.MID.SetBackgroundColour('medium gray')
        self.MID.SetForegroundColour('white')
        self.buttonList.append(self.MID)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer = wx.GridBagSizer()
        sizer.Add(self.quicklabel, (0, 0), (1, 3), buttonalignment)
        sizer.Add(self.TLC, (1, 0), (1, 1), buttonalignment)
        sizer.Add(self.MTE, (1, 1), (1, 1), buttonalignment)
        sizer.Add(self.TRC, (1, 2), (1, 1), buttonalignment)
        sizer.Add(self.MLE, (2, 0), (1, 1), buttonalignment)
        sizer.Add(self.MID, (2, 1), (1, 1), buttonalignment)
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
                elif button.GetLabelText() == 'MTE':
                    self._rootparent.update_fixation_location(wx.Point2D(0, v_fov / 2))
                elif button.GetLabelText() == 'TRC':
                    self._rootparent.update_fixation_location(wx.Point2D(h_fov/2, v_fov/2))
                elif button.GetLabelText() == 'MRE':
                    self._rootparent.update_fixation_location(wx.Point2D(h_fov / 2, 0))
                elif button.GetLabelText() == 'BRC':
                    self._rootparent.update_fixation_location(wx.Point2D(h_fov/2, -v_fov/2))
                elif button.GetLabelText() == 'MBE':
                    self._rootparent.update_fixation_location(wx.Point2D(0, -v_fov/2))
                elif button.GetLabelText() == 'BLC':
                    self._rootparent.update_fixation_location(wx.Point2D(-h_fov/2, -v_fov/2))
                elif button.GetLabelText() == 'MLE':
                    self._rootparent.update_fixation_location(wx.Point2D(-h_fov/2, 0))
                elif button.GetLabelText() == 'MID':
                    self._rootparent.update_fixation_location(wx.Point2D(0, 0))
