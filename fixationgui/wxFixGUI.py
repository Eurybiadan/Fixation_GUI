
import os
import wx
import math
import wx.lib.agw.floatspin as FS
import cPickle as pickle
import string

from time import sleep
from ViewPane import ViewPane
from protocolPane import ProtocolPane
from controlPanel import ControlPanel
from LightCrafter import wxLightCrafterFrame
from multiprocessing import Queue
import threading


global correctDistortion
correctDistortion = False

# CORRELATION FOR DEGREE TO TFT SCREEN PIXELS ***CHANGES WITH Z PLACEMENT OF THE OPTOTUNE****
global scrnpxpdeg
scrnpxpdeg=20
# CORRECTION FOR THE DISTORTION IN THE SYSTEM
global distort
distort=float(0)


# Sets Up The Class For The Program And Creates The Window
class wxFixationFrame(wx.Frame):
    
    def __init__(self,parent=None,fovQueue=None,captureQueue=None,id=wx.ID_ANY):
        wx.Frame.__init__(self,parent,id,'Automated Fixation Graphical User Interface')

        if fovQueue is None and captureQueue is None:
            self.Standalone = True
        else:
            self.Standalone = False
            self.MainSaviorFrame = parent

        self.withSerial = False
       
        # Initial Conditions
        self.horz_loc=0.0
        self.vert_loc=0.0
        self.diopter_value=0.0
        self._eyesign=-1

        self._locationfname = None
        self._locationpath  = None
        self._locfileobj    = None
        self.ArduinoSerial  = None
        
        self.header_dir = ""
        self.filename = ""
        self.SaveLoc = True
        
        # Allows Exit Button to Close Serial Communication
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        
        # Allows For Arrow Keys And Keys In General
        self.Bind(wx.EVT_CHAR_HOOK, self.OnKeyPress)

        self.initProtocolPanel(self)
        self.initControlPanel(self)
        self.initViewPane(self)
        
        # Handles mouse motion, presses, and wheel motions
        self.viewpane.Bind(wx.EVT_MOTION, self.OnMouseMotion)
        self.viewpane.Bind(wx.EVT_LEFT_DOWN, self.OnLeftMouseButton)
        self.viewpane.Bind(wx.EVT_RIGHT_DOWN, self.OnRightMouseButton)
        self.viewpane.Bind(wx.EVT_RIGHT_UP, self.OnRightMouseButton)
        self.Bind(wx.EVT_MOUSEWHEEL,self.OnMouseWheel)
        
        # Bind to any changes in the rotation slider
        self.control._iminitpane.BindTo(self.OnRotationSlider)
                
        horzsizer=wx.BoxSizer(wx.HORIZONTAL)

        horzsizer.Add(self.protocolpane,proportion=0,flag=wx.ALIGN_LEFT|wx.EXPAND)
        horzsizer.Add(self.imagespace,proportion=0,flag=wx.ALIGN_CENTER|wx.EXPAND)
        horzsizer.Add(self.control,proportion=0,flag=wx.ALIGN_RIGHT|wx.EXPAND)
        
        self.initMenu()
        
        # Displays Main Panel
        self.SetSizerAndFit(horzsizer)
        self.Layout()
        self.Centre()

        # Spawn the LightCrafter Canvas.
        self.LCCanvas = wxLightCrafterFrame()
        self.LCCanvas.Show()


        if self.Standalone is False:
##            print "Not standlone."
            try:
                fovQueue.get(False,0)
                captureQueue.get(False,0)
            except:
                pass
            # Spawn the pair of listener threads so we can detect changes in the comm Queues passed by Savior
            self.fovListener  = QueueListener(fovQueue,self.SetFOV) # This will recieve a tuple of sizes
            self.fovListener.start()
            self.captListener = QueueListener(captureQueue,self.MarkLocation) # This will recieve a simple 1 value
            self.captListener.start()


    def initViewPane(self, parent):
        # Setting up the ViewPane
        self.imagespace=wx.Panel(parent, wx.ID_ANY)
        self.imagespace.SetBackgroundColour('black')
        self.viewpane=ViewPane(self.imagespace,size=(513,513))
        
        # Create left label
        ltext=wx.Font(13, wx.SWISS,wx.NORMAL,wx.BOLD,False)
        left_text='\n\nN\na\ns\na\nl'
        self.l_text=wx.StaticText(self.imagespace,wx.ID_ANY,left_text,style=wx.ALIGN_CENTER)
        self.l_text.SetForegroundColour('white')
        self.l_text.SetFont(ltext)

        # Create top label
        stext=wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD, False)
        superior=wx.StaticText(self.imagespace,wx.ID_ANY,'Superior',style=wx.ALIGN_CENTER)
        superior.SetForegroundColour('white')
        superior.SetFont(stext)
        
        # Create bottom label
        stext=wx.Font(13, wx.SWISS, wx.NORMAL, wx.BOLD, False)
        inferior=wx.StaticText(self.imagespace,wx.ID_ANY,'Inferior',style=wx.ALIGN_CENTER)
        inferior.SetForegroundColour('white')
        inferior.SetFont(stext)
        
        # Create right label
        rtext=wx.Font(13, wx.SWISS,wx.NORMAL,wx.BOLD,False)
        right_text='T\ne\nm\np\no\nr\na\nl'
        self.r_text=wx.StaticText(self.imagespace,wx.ID_ANY,right_text,style=wx.ALIGN_CENTER)
        self.r_text.SetForegroundColour('white')
        self.r_text.SetFont(rtext)
        
        horzsizer=wx.BoxSizer(wx.HORIZONTAL)
        vertsizer=wx.BoxSizer(wx.VERTICAL)
        # Insert left label
        horzsizer.Add(self.l_text,  proportion=0, flag=wx.ALIGN_LEFT|wx.CENTER)
        
        # The "center panel" is now a vertcontrol sizer- insert top, viewpane, and bottom pieces
        vertsizer.Add(superior,proportion=0, flag=wx.ALIGN_TOP|wx.CENTER)
        vertsizer.Add(self.viewpane,   0,wx.ALIGN_CENTER|wx.ALL)
        vertsizer.Add(inferior,proportion=0, flag=wx.ALIGN_BOTTOM|wx.CENTER)
        
        # Insert the vertcontrol sizer
        horzsizer.Add(vertsizer, 0, wx.ALIGN_CENTER|wx.ALL)
        # Insert right label
        horzsizer.Add(self.r_text,  proportion=0, flag=wx.ALIGN_RIGHT|wx.CENTER)

        self.imagespace.SetSizer(horzsizer)
        

    def initProtocolPanel(self,parent):
        self.protocolpane = ProtocolPane(parent,id=wx.ID_ANY)
        
    def initControlPanel(self,parent):
        
        self.control=ControlPanel( parent, id=wx.ID_ANY, withSer=self.withSerial)

        # Bind all the events to the control panel
        self.control.vertcontrol.Bind(FS.EVT_FLOATSPIN,self.OnVertSpin)
        self.control.horzcontrol.Bind(FS.EVT_FLOATSPIN,self.OnHorzSpin)
        
        self.control.OS.Bind(wx.EVT_RADIOBUTTON, self.OnEyeSelect)
        self.control.OD.Bind(wx.EVT_RADIOBUTTON, self.OnEyeSelect)
        
        self.control._iminitpane.selectim.Bind(wx.EVT_BUTTON, self.OnButton)
        self.control._iminitpane.initalign.Bind(wx.EVT_BUTTON, self.OnButton)
        
        self.control.anchorbut.Bind(wx.EVT_BUTTON, self.OnButton)
        self.control.resetlocs.Bind(wx.EVT_BUTTON, self.OnButton)
        
    
    # Menu Bar
    def initMenu(self):
        
        # System Alignment Options
        self.id_rec_ser  = 10001
        self.id_save_on  = 10002
        self.id_save_off  = 10003
        self.id_on_fill  = 10011
        self.id_off_fill = 10012
        self.id_on_align = 10021
        self.id_off_align= 10022
        self.id_on_grid  = 10031
        self.id_off_grid = 10032
        self.id_save_proto_loc = 10004
        self.id_open_proto = 10005
        self.id_clear_proto = 10006
        
        # Creates Menu Bar
        menubar=wx.MenuBar()
        fileMenu=wx.Menu()
        protoMenu=wx.Menu()
        alignmentMenu=wx.Menu()
        menubar.Append(fileMenu,'File')
        menubar.Append(protoMenu,'Protocol')
        menubar.Append(alignmentMenu,'Alignment')

        # Open a protocol
        protoMenu.Append(self.id_save_proto_loc,'Protocol Save Location...\t')
        self.Bind(wx.EVT_MENU,self.OnSaveProtocolLoc,id=self.id_save_proto_loc)
        protoMenu.Append(self.id_open_proto,'Open Protocol...\t')
        self.Bind(wx.EVT_MENU,self.OnOpenProtocol,id=self.id_open_proto)
        protoMenu.Append(self.id_clear_proto,'Clear Protocol\t')
        self.Bind(wx.EVT_MENU,self.OnClearProtocol,id=self.id_clear_proto)

        # File Option
        
        self.saveMenu=wx.Menu()
        self.saveoff=self.saveMenu.AppendRadioItem(self.id_save_off,'Off')
        self.Bind(wx.EVT_MENU,self.OnSavePress,self.saveoff)
        self.saveon=self.saveMenu.AppendRadioItem(self.id_save_on,'On')
        self.saveon.Check(True)
        self.Bind(wx.EVT_MENU,self.OnSavePress,self.saveon)
        fileMenu.AppendMenu(wx.ID_ANY,'Save On Record',self.saveMenu)
        
#         self.Bind(wx.EVT_MENU,sel)
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_EXIT,'Exit\tCtrl+Q')
        self.Bind(wx.EVT_MENU,self.OnQuit,id=wx.ID_EXIT)

        # Open a background image
        alignmentMenu.Append(wx.ID_OPEN,'Open Background Image...\tCtrl+B')
        self.Bind(wx.EVT_MENU,self.OnOpenBkgrdIm,id=wx.ID_OPEN)
        
        # Fill Screen
        self.fillMenu=wx.Menu()
        self.off_fill=self.fillMenu.AppendRadioItem(self.id_off_fill,'Off')
        self.Bind(wx.EVT_MENU,self.OnFillPress,self.off_fill)
        self.on_fill=self.fillMenu.AppendRadioItem(self.id_on_fill,'On')
        self.Bind(wx.EVT_MENU,self.OnFillPress,self.on_fill)
        alignmentMenu.AppendMenu(wx.ID_ANY,'Fill Screen',self.fillMenu)
        # Alignment
        self.alignMenu=wx.Menu()
        self.off_align=self.alignMenu.AppendRadioItem(self.id_off_align,'Off')
        self.Bind(wx.EVT_MENU,self.OnAlignPress,self.off_align)
        self.on_align=self.alignMenu.AppendRadioItem(self.id_on_align,'On')
        self.Bind(wx.EVT_MENU,self.OnAlignPress,self.on_align)
        alignmentMenu.AppendMenu(wx.ID_ANY,'Alignment',self.alignMenu)
        # Grid
        self.gridMenu=wx.Menu()
        self.off_grid=self.gridMenu.AppendRadioItem(self.id_off_grid,'Off')
        self.Bind(wx.EVT_MENU,self.OnGridPress,self.off_grid)
        self.on_grid=self.gridMenu.AppendRadioItem(self.id_on_grid,'On')
        self.Bind(wx.EVT_MENU,self.OnGridPress,self.on_grid)
        alignmentMenu.AppendMenu(wx.ID_ANY,'Grid',self.gridMenu)
                
        # Compounds the Menu Bar
        self.SetMenuBar(menubar)
        
        # If serial isn't enabled, disable these options.
        if self.withSerial is False:
            self.saveoff.Enable(False)
            self.saveoff.Check(True) # Check off when we don't let it run.
            self.saveon.Enable(False)
            self.off_fill.Enable(False)
            self.on_fill.Enable(False)
            self.on_align.Enable(False)
            self.off_align.Enable(False)
            self.on_grid.Enable(False)
            self.off_grid.Enable(False)

    
    def OnSavePress(self,event):
        if self.withSerial:
            if event.GetId() == self.id_save_on:
##                print "Enabling saving location..."
                self.SaveLoc = True
            elif event.GetId() == self.id_save_off:
##                print "Disabling saving location..."
                self.SaveLoc = False
                        
    # Fill Screen
    def OnFillPress(self,event):
        if self.withSerial:
            if event.GetId() == self.id_on_fill:
                self.ArduinoSerial.write((7,1,1))
            elif event.GetId() == self.id_off_fill:
                self.ArduinoSerial.write((7,2,1))
                                
    # Alignment
    def OnAlignPress(self,event):
        if self.withSerial:
            if event.GetId() == self.id_on_align:
                self.ArduinoSerial.write((8,1,1))
            elif event.GetId() == self.id_on_align:
                self.ArduinoSerial.write((8,2,1))
                
    # Grid
    def OnGridPress(self,event):
        if self.withSerial:
            if event.GetId() == self.id_on_grid:
                self.ArduinoSerial.write((9,1,1))
            elif event.GetId() == self.id_off_grid:
                self.ArduinoSerial.write((9,2,1))
# End of Menu Bar

    
    def OnRotationSlider(self, rotation):
        self.viewpane.SetBkgrdRotate(rotation)
        
    def OnMouseMotion(self,event):
        pos = event.GetPosition()
        
        self.viewpane.SetMouseLoc(pos, self._eyesign)

        if wx.MouseEvent.LeftIsDown(event):
            # Convert to degrees
            self.horz_loc, self.vert_loc = self.viewpane.ToDegrees(pos) 
            self.UpdateFixLoc()
        elif wx.MouseEvent.RightIsDown(event) and self.viewpane.GetState()==1:
            self.viewpane.SetBkgrdPan(pos)

    def OnLeftMouseButton(self,event):
        pos = event.GetPosition()
        
        self.viewpane.SetMouseLoc(pos, self._eyesign)
        # Convert to degrees
        self.horz_loc, self.vert_loc = self.viewpane.ToDegrees(pos) 
        self.UpdateFixLoc()
    
    # To ensure we capture the initial offset from the origin of the image during a panning movement.
    def OnRightMouseButton(self,event):
        pos = event.GetPosition()
        if event.RightDown():
            self.viewpane.SetMouseOffset(wx.Point2DFromPoint(pos))
        elif event.RightUp():
            self.viewpane.SetMouseOffset(None)
            
    def OnMouseWheel(self,event):
        if self.viewpane.GetState() is 1 or self.viewpane.GetState() is 2:
            self.viewpane.SetBkgrdScale(math.copysign(1.0,event.GetWheelRotation())*.01)

    def OnButton(self,evt):
        button = evt.GetEventObject()
            
        # If the user clicked on Select Image
        if button is self.control._iminitpane.selectim:
            self.OnOpenBkgrdIm(None)
        elif button is self.control._iminitpane.initalign:
            
            state = self.viewpane.GetState() + 1
            
            if state == 2:
                self.viewpane.SetPanAnchor()
            elif state == 3: # If they hit the button after the initialization, restart the process.
                state = 0
                
            # Update the states in the two panels
            self.control.SetState(state)
            self.viewpane.SetState(state)
        elif button is self.control.resetlocs:
            self.viewpane.ClearLocations()
            self._locationfname = None
        
        elif button is self.control.anchorbut: 
##            print "Was: "+str(self._intercept)
            tmp= self.DegToLCDPix(self.horz_loc,self.vert_loc)
            offset = wx.Point2D(tmp[0],tmp[1])
##            print "Offset: "+ str(offset)
            #print "New: "+str(self._intercept+offset)
            # Update new center location
            #self._intercept = self._intercept+offset
            
            #self._intercept = wx.Point(round(self._intercept.x), round(self._intercept.y))
            self.LCCanvas.SetFixationCenter( offset )
            self.UpdateFixLoc(wx.Point2D(0,0)) #With the new intercept chosen, snap to that center
            
            
        else:
            pass    
        
    def UpdateFixLoc(self, degrees=None):
        
        # If you don't pass in degrees as an argument,
        # then assume that we're using whatever the current degrees are.
        if degrees is None:
            degrees = wx.Point2D(self.horz_loc, self.vert_loc)
        else:
            self.horz_loc = degrees.x
            self.vert_loc = degrees.y
        # Update the respective GUIs
        self.viewpane.SetFixLocInDeg(degrees)
        
        self.control.vertcontrol.SetValue(degrees.y)
        self.control.horzcontrol.SetValue(degrees.x)

        x, y = self.DegToLCDPix(degrees.x,degrees.y)

        self.LCCanvas.SetFixationLocation( wx.Point2D(x,y) )

                        
    def SetVFOV(self, degrees):
        self.viewpane.SetVFOV(degrees)

    def SetHFOV(self, degrees):
        self.viewpane.SetHFOV(degrees)

    def OnSaveProtocolLoc(self, evt):
        
        #If it doesn't exist, then prompt for the location before continuing...
        dialog=wx.FileDialog(self,'Save Location List As:',"","",'CSV (Comma delimited)|*.csv',wx.SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal()==wx.ID_OK:
            self._locationpath=dialog.GetDirectory()
            self._locationfname=dialog.GetFilename()
            dialog.Destroy()
            
            self._locfileobj = open(self._locationpath + os.sep + self._locationfname,'w') # Write the header
            self._locfileobj.write("Eye,Horizontal Location,Vertical Location,Horizontal FOV,Vertical FOV\n")        
            self._locfileobj.close()    

    def OnOpenProtocol(self, evt):
        dialog=wx.FileDialog(self,'Select protocol file:',self.header_dir,'',
                                  'CSV files (*.csv)|*.csv', wx.FD_OPEN)

        if dialog.ShowModal()==wx.ID_OK:
            self.header_dir=dialog.GetDirectory()
            protofname = dialog.GetFilename()
            dialog.Destroy()

            protopath =self.header_dir+os.sep+protofname
            self.protocolpane.LoadProtocol(protopath)
        
##        self.UpdateProtocol(self.vert_loc,self.horz_loc)

    def OnClearProtocol(self,evt):
        dlg = wx.MessageDialog(None, 'Are you sure you want to clear the protocol?', 'Clear Protocol', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.protocolpane.ClearProtocol()
            self.viewpane.ClearLocations()
            self._locationfname = None

    def OnOpenBkgrdIm(self, evt):
        dialog=wx.FileDialog(self,'Select background image:',self.header_dir,self.filename,
                                  'Image files (*.jpg,*.jpeg,*.bmp,*.png,*.tif,*.tiff)| *.jpg;*.jpeg;*.bmp;*.png;*.tif;*.tiff|'+
                                  'JP(E)G images (*.jpg,*.jpeg)|*.jpg;*.jpeg|BMP images (*.bmp)|*.bmp' +
                                  '|PNG images (*.png)|*.png|TIF(F) images (*.tif,*.tiff)|*.tif;*.tiff',wx.FD_OPEN)
        if dialog.ShowModal()==wx.ID_OK:
            self.header_dir=dialog.GetDirectory()
            self.filename=dialog.GetFilename()
            dialog.Destroy()
            impath =self.header_dir+os.sep+self.filename

            bkgrdim = wx.EmptyBitmap( 1, 1 )
            bkgrdim.LoadFile( impath, wx.BITMAP_TYPE_ANY )
            self.viewpane.SetBkgrd(bkgrdim)
        
    def DegToLCDPix(self,deghorz,degvert):
        
        # Converts Degrees to Screen Pixels - X should be POSITIVE going left on screen for OD
        
        x=-deghorz*scrnpxpdeg
        
        y=-degvert*scrnpxpdeg
        
        return x,y

    def DistortionCorrect(self, x, y):
        # This method adjusts an input x and y
        # to account for the radial lens distortion, and returns
        # the x,y,and rad2 values.
        rad2=(x*x+y*y)
        y=y*(1+distort*rad2)
        x=x*(1+distort*rad2)
        x=math.trunc(x)
        y=math.trunc(y)
        
        return x,y,rad2

    def OnKeyPress(self,event):
        # Allows For Arrow Control Of The Cursor
        if event.GetKeyCode()==wx.WXK_NUMPAD_ADD:
            self.OnZoom(self)
        elif event.GetKeyCode()==wx.WXK_NUMPAD_SUBTRACT:
            self.zoom_out(self)
        if self.viewpane.align_on is True:
            self.OnImAlignArrow(event)
        elif self.viewpane.align_on is False:
            self.OnFixationArrow(event)

    def OnImAlignArrow(self,event):
        if event.ControlDown(): # The image can only be moved if Control is being held down!
            if event.GetKeyCode()==wx.WXK_DOWN:
                self.viewpane.pan_y=self.viewpane.pan_y+1
                self.viewpane.int_Graph()
            elif event.GetKeyCode()==wx.WXK_UP:
                self.viewpane.pan_y=self.viewpane.pan_y-1
                self.viewpane.int_Graph()
            elif event.GetKeyCode()==wx.WXK_LEFT:
                self.viewpane.pan_x=self.viewpane.pan_x-1
                self.viewpane.int_Graph()
            elif event.GetKeyCode()==wx.WXK_RIGHT:
                self.viewpane.pan_x=self.viewpane.pan_x+1
                self.viewpane.int_Graph()
        else:
            self.OnFixationArrow(event)
        event.Skip()

    def OnFixationArrow(self,event):
        if event.GetKeyCode()==wx.WXK_DOWN:
            if event.ShiftDown():
                self.vert_loc=self.vert_loc-1
                self.UpdateFixLoc()
            else:
                self.vert_loc=round(self.vert_loc-1/scrnpxpdeg,1)
                self.UpdateFixLoc()
        elif event.GetKeyCode()==wx.WXK_UP:
            if event.ShiftDown():
                self.vert_loc=self.vert_loc+1
                self.UpdateFixLoc()
            else:
                self.vert_loc=round(self.vert_loc+1/scrnpxpdeg,1)
                self.UpdateFixLoc()
        elif event.GetKeyCode()==wx.WXK_LEFT:
            if event.ShiftDown():
                self.horz_loc=round(self.horz_loc,1)
                self.UpdateFixLoc()
            else:
                self.horz_loc=round(self.horz_loc-1/scrnpxpdeg,1)
                self.UpdateFixLoc()
        elif event.GetKeyCode()==wx.WXK_RIGHT:
            if event.ShiftDown():
                self.horz_loc=round(self.horz_loc,1)
                self.UpdateFixLoc()
            else:
                self.horz_loc=round(self.horz_loc+1/scrnpxpdeg,1)
                self.UpdateFixLoc()
        else:
            event.Skip()

    def OnEyeSelect(self,event):
    # Changes Cursor And Location Names Based On OnEyeSelect Selected cursor
        state=str(self.control.OS.GetValue())
        if state=='True': # If it is OS, eyesign is -1
            self._eyesign=-1
            self.r_text.SetLabel('T\ne\nm\np\no\nr\na\nl')
            self.l_text.SetLabel(' \n \nN\na\ns\na\nl\n \n')
            self.control.horzcontrol.FlipLabels()
            self.UpdateFixLoc()
        elif state=='False': #If it is OD, eyesign is 1
            self._eyesign=1
            self.r_text.SetLabel(' \n \nN\na\ns\na\nl\n \n')
            self.l_text.SetLabel('T\ne\nm\np\no\nr\na\nl')
            self.control.horzcontrol.FlipLabels()
            self.UpdateFixLoc()

    def OnVertSpin(self,event):
        # Entering a vertical location value using the subclass
        y_ent=self.control.vertcontrol.GetValue()
        self.vert_loc=round(float(y_ent),2)
        self.UpdateFixLoc()

    def OnHorzSpin(self,event):
        # Entering a horizontal location value using the subclass
        x_ent=self.control.horzcontrol.GetValue()        
        self.horz_loc=round(float(x_ent),1)
        self.UpdateFixLoc()
        
    def MarkLocation(self, data):

        # "Poison pill" shutdown of the Fixation GUI.
        if data == -1:
            self.OnQuit(wx.EVT_CLOSE)
            return
        
       # Marks the current lcoation of the fixation target, and dumps it to a file
        self.viewpane.MarkLocation()
        self.UpdateProtocol( self.control.horzcontrol.GetLabelValue(),self.control.vertcontrol.GetLabelValue() )
        self.SaveLocation( self.control.horzcontrol.GetLabelValue(),self.control.vertcontrol.GetLabelValue() )

    def SetFOV(self, fov):

        if fov != -1:
            self.viewpane.SetFOV(fov)

    def UpdateColor(self,penColor, brushColor):
        # This method allows the user to change the color on the LightCrafter DLP.
        self.LCCanvas.SetFixationColor(penColor, brushColor)

    def UpdateCursor(self, cursor):
        # This method allows the user to change the cursor type on the LightCrafter DLP.
        self.LCCanvas.SetFixationCursor(cursor)

    def UpdateCursorSize(self, size):
        # This method allows the user to change the cursor size on the LightCrafter DLP.
        self.LCCanvas.SetFixationSize(size)

    def ResetFixLoc(self,event):
        # Reset fixation target Location 
        self.horz_loc=0.0
        self.vert_loc=0.0
        
        self.UpdateFixLoc()

    def UpdateProtocol(self, horzloc, vertloc):    
        # Send a query to our protocol pane, marking a new location if there is one, or fulfilling a protocol requirement
        self.protocolpane.UpdateProtocol( (self.control.horzcontrol.GetLabelValue(),self.control.vertcontrol.GetLabelValue()), self._eyesign, self.viewpane.GetFOV() )
        

    def SaveLocation(self, horzloc, vertloc):
        
        # Create a file that we will dump all of the relevant information to
        if self._locationfname is None:
            #If it doesn't exist, then prompt for the location before continuing...
            dialog=wx.FileDialog(self,'Save Location List As:',"","",'CSV (Comma delimited)|*.csv',wx.SAVE|wx.FD_OVERWRITE_PROMPT)
            if dialog.ShowModal()==wx.ID_OK:
                self._locationpath=dialog.GetDirectory()
                self._locationfname=dialog.GetFilename()
                dialog.Destroy()

                self._locfileobj = open(self._locationpath + os.sep + self._locationfname,'w') # Write the header
                self._locfileobj.write("Eye,Horizontal Location,Vertical Location,Horizontal FOV,Vertical FOV\n")        
                self._locfileobj.close()
                
            else:
                return
        
        try:
            self._locfileobj = open(self._locationpath + os.sep + self._locationfname,'a')
        except IOError: # If there is an exception, then the file is already open, or is being written to
            if self._locfileobj.closed:
                pass
##                print "Failed to open location dump file!"
                return
            else:
                pass
##                print "File is already open, continuing..."

        if self.SaveLoc is False: # If we're not supposed to save the location, just save the FOV
            horzloc = ""
            vertloc = ""

        if self._eyesign == -1:
            eye = "OS"
        else:
            eye = "OD"
    
        self._locfileobj.write(eye+","+horzloc+","+vertloc+","+str(self.viewpane.GetHFOV())+","+str(self.viewpane.GetVFOV())+"\n")        
        
        self._locfileobj.close()
        

        
# Saves The Aligned ViewPane
    def SaveViewPane(self,event):
        context=wx.ClientDC(self.imagespace)
        memory=wx.MemoryDC()
        x,y=self.imagespace.ClientSize
        bitmap=wx.EmptyBitmap(x,y,wx.ID_ANY)
        memory.SelectObject(bitmap)
        memory.Blit(0,0,x,y,context,0,0)
        memory.SelectObject(wx.NullBitmap)
        wx.InitAllImageHandlers()
        self.filename=''
        dialog=wx.FileDialog(self,'Save Aligned ViewPane As:',self.save_image_dir,self.filename,'*.jpeg*',wx.SAVE|wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal()==wx.ID_OK:
            self.save_image_dir=dialog.GetDirectory()
            self.filename=dialog.GetFilename()
            dialog.Destroy()
        bitmap.SaveFile(self.filename + '.jpeg' ,wx.BITMAP_TYPE_JPEG)

# Initiates The Base Diopter Value
    def diopterbase(self,event):
        #if self.withSerial:
            #self.opt.write((2,1))
        sleep(0.05)

# Exits The Application
    def OnQuit(self,event):

        
        if self.withSerial:
            # self.ArduinoSerial.close()
            self.control._optopane.OnClose(event)
        #self.settingsSave(self.ScreenPort, self.opto.getPort())
        #print "Saved settings, and exiting..."

        self.LCCanvas.Destroy()
        self.Destroy()

# This thread class generically listens to a queue, and passes what it receives to a specified function.
class QueueListener(threading.Thread):

    def __init__(self, queue, func):
                 
        threading.Thread.__init__(self)

        self.queue = queue
        self.callback = func
##        print "Spawning queue thread"

    def run(self):
        while True:
            recv = self.queue.get()

            self.callback(recv)
##            print "Recieved message: "
##            print recv
            if recv == -1:
##                print "Recieved posion pill, dying..."
                return
            


#Shows The Window
if __name__=='__main__':
    app=wx.App(redirect=False)
    frame=wxFixationFrame(None)
    frame.Show()
    app.MainLoop()
