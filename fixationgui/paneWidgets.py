'''
Created on Sep 20, 2013

@author: Robert F Cooper
'''

import wx
from array import array
from serial import SerialException
    
    
class CursorPanel(wx.Panel):
    '''
    This class encapsulates the cursor modifying behavior of the Fixation GUI software.
    '''


    def __init__(self,parent,rootparent,id=wx.ID_ANY,pos=wx.DefaultPosition,size=wx.DefaultSize,style=wx.SIMPLE_BORDER,name='Cursor Control'):

        '''
        Constructor
        '''
        super(CursorPanel,self).__init__(parent,id,pos,size,style,name)
        self.SetBackgroundColour('black')
        self._rootparent = rootparent
        
        labelFont = wx.Font(9,wx.SWISS,wx.NORMAL,wx.BOLD,False)
        
        # Create the sizer for the miniPanel
        minipanesizer = wx.BoxSizer(wx.VERTICAL)
        
        widgetLabel = wx.StaticText(self,wx.ID_ANY,self.GetName())
        widgetLabel.SetForegroundColour('white')
        widgetLabel.SetFont(wx.Font(9,wx.SWISS,wx.NORMAL,wx.BOLD,False))
        
        minipanesizer.Add(widgetLabel,0,wx.ALIGN_CENTER)
        
        # Create pens for this class
        self.BLKPEN = wx.Pen(wx.BLACK,3,wx.SOLID)
        self.WHITEPEN = wx.Pen(wx.WHITE,3,wx.SOLID)
        self.MAGPEN = wx.Pen( (255,0,255),3,wx.SOLID)
        self.REDPEN = wx.Pen(wx.RED,3,wx.SOLID)
        self.GRNPEN = wx.Pen(wx.Color(0,255,0,255),3,wx.SOLID)
        self.BLUPEN = wx.Pen(wx.BLUE,3,wx.SOLID)
        self.YLWPEN = wx.Pen('Yellow',3,wx.SOLID)
        self.GRAYPEN  = wx.Pen(wx.Color(75,75,75,255),3,wx.SOLID)
        
        # Create brushes for this class
        self.WHTBRSH_TRANS = wx.Brush(wx.WHITE,wx.TRANSPARENT)
        self.MAGENTABRSH = wx.Brush( (255,0,255),wx.SOLID)
        self.REDBRSH = wx.Brush(wx.RED,wx.SOLID)
        self.GREENBRSH = wx.Brush(wx.Color(0,255,0,255),wx.SOLID)
        self.BLUEBRSH = wx.Brush(wx.BLUE,wx.SOLID)
        self.YELLOWBRSH = wx.Brush('Yellow',wx.SOLID)
        self.WHITEBRSH = wx.Brush(wx.WHITE,wx.SOLID)
        self.GRAYBRSH  = wx.Brush(wx.Color(75,75,75,255),wx.SOLID)
        
        # Constants for transmission to the Arduino
        self.ARDMAG=63519
        self.ARDRED=7
        self.ARDYLW=65504
        self.ARDGRN=2016
        self.ARDBLU=2047
        self.ARDWHT=65535
        
        self.CROSS   = 0
        self.SQCLOSE = 1
        self.SQOPEN  = 2
        self.CIRCLE  = 3
        
        self._iconsize = 25
        self._curpencolor = self.GRNPEN
        self._curbrshcolor = self.GREENBRSH
        
        
        # Make the cursor types for each button.
        
        # Cross (Serial command: 6,3)
        self._cross = wx.EmptyBitmap(self._iconsize,self._iconsize)
        crosspoints = [(12, 2, 12, 23), (2, 12, 23, 12)]
        dc = wx.MemoryDC()
        dc.SelectObject(self._cross)
        dc.SetPen(self._curpencolor)
        dc.SetBrush(self.WHTBRSH_TRANS)
        dc.DrawLineList(crosspoints)
        
        self._crossButton = wx.BitmapButton(self,wx.ID_ANY,self._cross,style=wx.BU_AUTODRAW, name='Cross')

        # Default is the cross button.
        self._cursorpressed = self._crossButton
        
        # Open Square (Serial command: 6,1,1)
        self._osquare = wx.EmptyBitmap(self._iconsize,self._iconsize)
        dc.SelectObject(self._osquare)
        dc.SetPen(self.GRAYPEN)
        dc.DrawRectangle(4,4,17,17)
        
        self._osquareButton = wx.BitmapButton(self,wx.ID_ANY,self._osquare,style=wx.BU_AUTODRAW, name='Open Square')
        
        # Closed Square (Serial command: 6,0,1)
        
        self._csquare = wx.EmptyBitmap(self._iconsize,self._iconsize)
        dc.SelectObject(self._csquare)
        dc.SetBrush(self.GRAYBRSH)
        dc.DrawRectangle(4,4,17,17)
        
        self._csquareButton = wx.BitmapButton(self,wx.ID_ANY,self._csquare,style=wx.BU_AUTODRAW, name='Closed Square')
        
        # Closed Circle (Serial command: 6,2,1)
        self._circle = wx.EmptyBitmap(self._iconsize,self._iconsize)
        dc.SelectObject(self._circle)
        dc.SetBrush(self.GRAYBRSH)
        dc.DrawCircle(12,12,9)
        
        self._circleButton = wx.BitmapButton(self,wx.ID_ANY,self._circle,style=wx.BU_AUTODRAW, name='Square')
        
        del dc

        self._crossButton.Bind(wx.EVT_BUTTON,self.OnButton)
        self._osquareButton.Bind(wx.EVT_BUTTON,self.OnButton)
        self._csquareButton.Bind(wx.EVT_BUTTON,self.OnButton)
        self._circleButton.Bind(wx.EVT_BUTTON,self.OnButton)

        cursorsizer = wx.BoxSizer(wx.HORIZONTAL)
        
        cursorsizer.Add(self._crossButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._osquareButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._csquareButton, 0, wx.ALL, 2)
        cursorsizer.Add(self._circleButton, 0, wx.ALL, 2)

        
        
        
        self.buttonList = []
        
        # Magenta
        magentaico = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,0,255,255)
        magentaicodown = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,0,255,255)        
        magButton  = wx.BitmapButton(self,wx.ID_ANY,magentaico,style=wx.BU_AUTODRAW, name='Magenta')
        magButton.SetBitmapDisabled(magentaicodown)
        self.buttonList.append(magButton)
        # Red
        redico     = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,0,0,255)
        redicodown     = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,0,0,255)
        redButton  = wx.BitmapButton(self,wx.ID_ANY,redico,style=wx.BU_AUTODRAW, name='Red')
        redButton.SetBitmapDisabled(redicodown)
        self.buttonList.append(redButton)
        # Yellow
        yellowico  = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,255,0,255)
        yellowicodown  = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,255,0,255)
        yelButton  = wx.BitmapButton(self,wx.ID_ANY,yellowico,style=wx.BU_AUTODRAW, name='Yellow')
        yelButton.SetBitmapDisabled(yellowicodown)
        self.buttonList.append(yelButton)
        # Green
        greenico   = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,0,255,0,255)
        greenicodown   = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,0,255,0,255)
        grnButton  = wx.BitmapButton(self,wx.ID_ANY,greenico,style=wx.BU_AUTODRAW, name='Green')
        grnButton.SetBitmapDisabled(greenicodown)
        self.buttonList.append(grnButton)        
        # Blue
        blueico    = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,0,0,255,255)
        blueicodown    = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,0,0,255,255)
        bluButton  = wx.BitmapButton(self,wx.ID_ANY,blueico,style=wx.BU_AUTODRAW, name='Blue')
        bluButton.SetBitmapDisabled(blueicodown)
        self.buttonList.append(bluButton)
        # White
        whiteico   = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,255,255,255)
        whiteicodown   = wx.EmptyBitmapRGBA(self._iconsize,self._iconsize,255,255,255,255)
        
        whtButton  = wx.BitmapButton(self,wx.ID_ANY,whiteico,style=wx.BU_AUTODRAW, name='White')
        whtButton.SetBitmapDisabled(whiteicodown)
        self.buttonList.append(whtButton)
        
        # Add each button to the sizer, with a 2 pixel border around each.
        colorsizer = wx.BoxSizer(wx.HORIZONTAL)
        for button in self.buttonList:
            colorsizer.Add(button,0, wx.ALL, 2)
    
        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON,self.OnButton)

    
        sizelabel  = wx.StaticText(self, id=wx.ID_ANY,  label='Cursor Size:')
        sizelabel.SetForegroundColour('white')
        sizelabel.SetFont(labelFont)
        sizeslider = wx.Slider(self,value = 5, minValue = 1, maxValue = 20,size=(-1,-1),style=wx.SL_HORIZONTAL|wx.SL_LABELS|wx.SL_BOTTOM)
        sizeslider.SetForegroundColour('white')
        sizeslider.SetFont(labelFont)
        sizeslider.Bind(wx.EVT_SCROLL, self.OnSliderScroll)
    
        sizesizer = wx.BoxSizer(wx.HORIZONTAL)
        sizesizer.Add(sizelabel,wx.ALIGN_TOP,wx.RIGHT|wx.LEFT,2)
        sizesizer.Add(sizeslider,wx.CENTER,wx.RIGHT|wx.LEFT,2)
        
        minipanesizer.Add(colorsizer)
        minipanesizer.Add(cursorsizer,1,wx.ALIGN_RIGHT)
        minipanesizer.Add(sizesizer,1,wx.EXPAND)
        
        self.SetSizerAndFit(minipanesizer)
        
        
        
    
    def RedrawCursors(self):
        
        self._cross = wx.EmptyBitmap(self._iconsize,self._iconsize)
        crosspoints = [(12, 2, 12, 23), (2, 12, 23, 12)]
        dc = wx.MemoryDC()
        dc.SelectObject(self._cross)
        if self._cursorpressed is self._crossButton:
            dc.SetPen(self._curpencolor)
            dc.SetBrush(self.WHTBRSH_TRANS)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.WHTBRSH_TRANS)
        dc.DrawLineList(crosspoints)
        
        self._crossButton.SetBitmapLabel(self._cross)
                
        # Open Square
        self._osquare = wx.EmptyBitmap(self._iconsize,self._iconsize)
        dc.SelectObject(self._osquare)
        if self._cursorpressed is self._osquareButton:
            dc.SetPen(self._curpencolor)
        else:
            dc.SetPen(self.GRAYPEN)
        dc.DrawRectangle(4,4,17,17)
        
        self._osquareButton.SetBitmapLabel(self._osquare)
        
        # Closed Square
        self._csquare = wx.EmptyBitmap(self._iconsize,self._iconsize)
        dc.SelectObject(self._csquare)
        if self._cursorpressed is self._csquareButton:
            dc.SetBrush(self._curbrshcolor)
            dc.SetPen(self._curpencolor)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.GRAYBRSH)
        
        dc.DrawRectangle(4,4,17,17)
        
        self._csquareButton.SetBitmapLabel(self._csquare)
        
        # Closed Circle
        self._circle = wx.EmptyBitmap(self._iconsize,self._iconsize)
        dc.SelectObject(self._circle)
        if self._cursorpressed is self._circleButton:
            dc.SetBrush(self._curbrshcolor)
            dc.SetPen(self._curpencolor)
        else:
            dc.SetPen(self.GRAYPEN)
            dc.SetBrush(self.GRAYBRSH)
        dc.DrawCircle(12,12,9)
        
        self._circleButton.SetBitmapLabel(self._circle)
        
        del dc
    
    def OnButton(self,evt):
        pressed = evt.GetEventObject()
        # Check if it was one of the colors
        for button in self.buttonList:
            if pressed is button:
##                print "You pressed "+button.GetName()+"!"
                if button.GetName() == "Magenta": # Magenta is 63519
                    self._curpencolor  = self.MAGPEN
                    self._curbrshcolor = self.MAGENTABRSH
                    self._rootparent.UpdateColor(self._curpencolor, self._curbrshcolor)
                elif button.GetName() == "Red": # Red is 63488
                    self._curpencolor  = self.REDPEN
                    self._curbrshcolor = self.REDBRSH
                    self._rootparent.UpdateColor(self._curpencolor, self._curbrshcolor)
                elif button.GetName() == "Yellow": # Yellow is 65504
                    self._curpencolor  = self.YLWPEN
                    self._curbrshcolor = self.YELLOWBRSH
                    self._rootparent.UpdateColor(self._curpencolor, self._curbrshcolor)
                elif button.GetName() == "Green": # Green is 2016
                    self._curpencolor  = self.GRNPEN
                    self._curbrshcolor = self.GREENBRSH
                    self._rootparent.UpdateColor(self._curpencolor, self._curbrshcolor)
                elif button.GetName() == "Blue": # Blue is 2047
                    self._curpencolor  = self.BLUPEN
                    self._curbrshcolor = self.BLUEBRSH
                    self._rootparent.UpdateColor(self._curpencolor, self._curbrshcolor)
                elif button.GetName() == "White": # White is 65535
                    self._curpencolor  = self.WHITEPEN
                    self._curbrshcolor = self.WHITEBRSH
                    self._rootparent.UpdateColor(self._curpencolor, self._curbrshcolor)
                break 
        
        
        if pressed is self._crossButton:
            self._rootparent.UpdateCursor(self.CROSS)
            self._cursorpressed = self._crossButton
        elif pressed is self._osquareButton:
            self._rootparent.UpdateCursor(self.SQOPEN)
            self._cursorpressed = self._osquareButton
        elif pressed is self._csquareButton:
            self._rootparent.UpdateCursor(self.SQCLOSE)
            self._cursorpressed = self._csquareButton
        elif pressed is self._circleButton:
            self._rootparent.UpdateCursor(self.CIRCLE)
            self._cursorpressed = self._circleButton

        self.RedrawCursors()
        
    def OnSliderScroll(self, evt):
        
        obj = evt.GetEventObject()
        val = obj.GetValue()
        self._rootparent.UpdateCursorSize(val)
        
class ImInitPanel(wx.Panel):
    '''
    classdocs
    '''
    
    def __init__(self,parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1,-1), style=wx.SIMPLE_BORDER, name='Image Initialization Panel', port=None):
        wx.Panel.__init__(self,parent,id,pos,size,style,name)
        
        self.SetBackgroundColour('black')
        
        self.__deg_symbol=u'\N{DEGREE SIGN}'
        self._slider_val=0
        self._sliderObservers = []
        
        labelFont = wx.Font(11,wx.SWISS,wx.NORMAL,wx.BOLD,False)
        
        # Select Image Button
        self.selectim=wx.Button(self,label='Select Image',size=(-1,30))
        self.selectim.SetBackgroundColour('medium gray')
        self.selectim.SetForegroundColour('white')
        
        # Align ViewPane
        self.initalign=wx.Button(self,label='Initialization', size=(-1,30))
        self.initalign.SetBackgroundColour('medium gray')
        self.initalign.SetForegroundColour('white')
        
        butsizer=wx.BoxSizer(wx.HORIZONTAL)
        butsizer.Add(self.selectim, 1, wx.ALIGN_CENTER|wx.ALL,5 )
        butsizer.Add(self.initalign, 1, wx.ALIGN_CENTER|wx.ALL,5 )
        
        # Rotation slider
        self.rotlabel = wx.StaticText(self,wx.ID_ANY,'0.0'+self.__deg_symbol)
        self.rotlabel.SetForegroundColour('white')
        self.rotlabel.SetFont(labelFont)
        self.rotlabel.Hide()
        self.rotslider = wx.Slider(self,wx.ID_ANY, value=0,minValue=-20,maxValue=20)
        self.rotslider.SetTickFreq(1)
        
        self.Bind(wx.EVT_SCROLL,self.OnRotationSlider)
        
        rotsizer=wx.BoxSizer(wx.HORIZONTAL)
        rotsizer.Add(self.rotslider, 0, wx.ALIGN_CENTER)
        rotsizer.Add(self.rotlabel, 0, wx.ALIGN_CENTER)
        
        panesizer=wx.BoxSizer(wx.VERTICAL)
        
        panesizer.Add(butsizer,0,wx.ALIGN_CENTER)
        panesizer.Add(rotsizer,0,wx.ALIGN_CENTER)
        
        self.SetSizerAndFit(panesizer)
        self.rotslider.Hide()
        self.rotlabel.Hide()
        

    def SetState(self,state):
        
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
        
    def OnRotationSlider(self,event):
        if event.GetEventObject() is self.rotslider:
            self.SetRotationValue(event.GetPosition()/2.0)
            self.rotlabel.SetLabel(str(self._slider_val)+self.__deg_symbol )
            
    def SetRotationValue(self, val):
        self._slider_val = val
        for callback in self._sliderObservers:
            callback(self._slider_val)
            
    def GetRotationValue(self):
        return self._slider_val
    
    def BindTo(self, callback):
        self._sliderObservers.append(callback)
        
        
