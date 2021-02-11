import asyncore
import os
import wx
import math
import wx.lib.agw.floatspin as FS

from time import sleep
from ViewPane import ViewPane
from protocolPane import ProtocolPane
from controlPanel import ControlPanel
from LightCrafter import wxLightCrafterFrame
from PreferencesDialog import PreferencesDialog
import socket
import threading

myEVT_MESSAGE = wx.NewEventType()
EVT_MESSAGE = wx.PyEventBinder(myEVT_MESSAGE, 1)

myEVT_RETURN_MESSAGE = wx.NewEventType()
EVT_RETURN_MESSAGE = wx.PyEventBinder(myEVT_RETURN_MESSAGE, 2)


# Sets Up The Class For The Program And Creates The Window
class wxFixationFrame(wx.Frame):
    # The number of ppd of the screen we'll be projecting to (e.g. Lightcrafter, Projector, etc).
    SCREEN_PPD = 20

    # The increment steps we'll use.
    MINOR_INCREMENT = 0.5
    MAJOR_INCREMENT = 1

    def __init__(self, parent=None, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, 'Automated Fixation Graphical User Interface')

        self.withSerial = False

        # Initial Conditions
        self.curr_path = ''
        self.protopath = ''
        self.protopath_pcrash = 'start'
        self.tracker = -1
        self.horz_loc = 0.0
        self.vert_loc = 0.0
        self.diopter_value = 0.0
        self._eyesign = -1

        self._locationfname = None
        self._locationpath = None
        self._locfileobj = None
        self.ArduinoSerial = None

        self.header_dir = ""
        self.filename = ""
        self.SaveLoc = True

        # Allows Exit Button to Close Serial Communication
        self.Bind(wx.EVT_CLOSE, self.on_quit)

        # Allows For Arrow Keys And Keys In General
        self.Bind(wx.EVT_CHAR_HOOK, self.on_keyboard_press)

        self.initProtocolPanel(self)
        self.initControlPanel(self)
        self.initViewPane(self)

        # Handles mouse motion, presses, and wheel motions
        self.viewpane.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.viewpane.Bind(wx.EVT_LEFT_DOWN, self.on_left_mouse_button)
        self.viewpane.Bind(wx.EVT_RIGHT_DOWN, self.on_right_mouse_button)
        self.viewpane.Bind(wx.EVT_RIGHT_UP, self.on_right_mouse_button)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

        # Bind to any changes in the rotation slider
        self.control._iminitpane.BindTo(self.on_rotation_slider)

        horzsizer = wx.BoxSizer(wx.HORIZONTAL)

        horzsizer.Add(self.protocolpane, proportion=0, flag=wx.EXPAND)
        horzsizer.Add(self.imagespace, proportion=0, flag=wx.EXPAND)
        horzsizer.Add(self.control, proportion=0, flag=wx.EXPAND)

        self.init_menubar()

        # Displays Main Panel
        self.SetSizerAndFit(horzsizer)
        self.Layout()
        self.Centre()

        # Spawn the LightCrafter Canvas.
        self.LCCanvas = wxLightCrafterFrame()
        self.LCCanvas.Show()

        self.prev_cursor = self.LCCanvas.get_fixation_cursor()

        self.Bind(EVT_MESSAGE, self.handle_message)

        # Spawn the pair of listener threads so we can detect changes in the comm Queues passed by Savior
        self.fovListener = ConnListener(self)  # This will recieve a tuple of sizes
        self.fovListenerThread = threading.Thread(target=asyncore.loop, kwargs={'timeout': 1})
        self.fovListenerThread.setDaemon(True)
        self.fovListenerThread.start()

    def initViewPane(self, parent):
        # Setting up the ViewPane
        self.imagespace = wx.Panel(parent, wx.ID_ANY)
        self.imagespace.SetBackgroundColour('black')
        self.viewpane = ViewPane(self.imagespace, size=(513, 513))

        # Create left label
        ltext = wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
        left_text = '\n\nN\na\ns\na\nl'
        self.l_text = wx.StaticText(self.imagespace, wx.ID_ANY, left_text, style=wx.ALIGN_CENTER)
        self.l_text.SetForegroundColour('white')
        self.l_text.SetFont(ltext)

        # Create top label
        stext = wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
        superior = wx.StaticText(self.imagespace, wx.ID_ANY, 'Superior', style=wx.ALIGN_CENTER)
        superior.SetForegroundColour('white')
        superior.SetFont(stext)

        # Create bottom label
        stext = wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
        inferior = wx.StaticText(self.imagespace, wx.ID_ANY, 'Inferior', style=wx.ALIGN_CENTER)
        inferior.SetForegroundColour('white')
        inferior.SetFont(stext)

        # Create right label
        rtext = wx.Font(13, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD, False)
        right_text = 'T\ne\nm\np\no\nr\na\nl'
        self.r_text = wx.StaticText(self.imagespace, wx.ID_ANY, right_text, style=wx.ALIGN_CENTER)
        self.r_text.SetForegroundColour('white')
        self.r_text.SetFont(rtext)

        horzsizer = wx.BoxSizer(wx.HORIZONTAL)
        vertsizer = wx.BoxSizer(wx.VERTICAL)
        # Insert left label
        horzsizer.Add(self.l_text, proportion=0, flag=wx.CENTER)

        # The "center panel" is now a vertcontrol sizer- insert top, viewpane, and bottom pieces
        vertsizer.Add(superior, proportion=0, flag=wx.CENTER)
        vertsizer.Add(self.viewpane, 0, wx.ALIGN_CENTER | wx.ALL)
        vertsizer.Add(inferior, proportion=0, flag=wx.CENTER)

        # Insert the vertcontrol sizer
        horzsizer.Add(vertsizer, 0, wx.ALIGN_CENTER | wx.ALL)
        # Insert right label
        horzsizer.Add(self.r_text, proportion=0, flag=wx.CENTER)

        self.imagespace.SetSizer(horzsizer)

    def initProtocolPanel(self, parent):
        self.protocolpane = ProtocolPane(parent, id=wx.ID_ANY)

    def initControlPanel(self, parent):

        self.control = ControlPanel(parent, id=wx.ID_ANY)

        # Bind all the events to the control panel
        self.control.vertcontrol.Bind(FS.EVT_FLOATSPIN, self.on_vert_spin)
        self.control.horzcontrol.Bind(FS.EVT_FLOATSPIN, self.on_horz_spin)

        self.control.minorStep.Bind(FS.EVT_FLOATSPIN, self.on_minor_step)
        self.control.majorStep.Bind(FS.EVT_FLOATSPIN, self.on_major_step)

        self.control.OS.Bind(wx.EVT_RADIOBUTTON, self.on_eye_select)
        self.control.OD.Bind(wx.EVT_RADIOBUTTON, self.on_eye_select)

        self.control._iminitpane.selectim.Bind(wx.EVT_BUTTON, self.on_button_press)
        self.control._iminitpane.initalign.Bind(wx.EVT_BUTTON, self.on_button_press)

    # Menu Bar
    def init_menubar(self):

        # System Alignment Options
        self.id_rec_ser = 10001
        self.id_save_on = 10002
        self.id_save_off = 10003
        self.id_on_fill = 10011
        self.id_off_fill = 10012
        self.id_on_align = 10021
        self.id_off_align = 10022
        self.id_on_grid = 10031
        self.id_off_grid = 10032
        self.id_on_toggle = 10041
        self.id_off_toggle = 10042
        self.id_save_proto_loc = 10004
        self.id_open_proto = 10005
        # JG 2/5
        self.id_open_proto_pcrash = 10006
        #
        self.id_clear_proto = 10007

        # Creates Menu Bar
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        protoMenu = wx.Menu()
        targetMenu = wx.Menu()
        menubar.Append(fileMenu, 'File')
        menubar.Append(protoMenu, 'Protocol')
        menubar.Append(targetMenu, 'Target')

        # Open a protocol
        protoMenu.Append(self.id_save_proto_loc, 'Set Protocol Save Location...\t')
        self.Bind(wx.EVT_MENU, self.on_set_save_protocol_location, id=self.id_save_proto_loc)
        protoMenu.Append(self.id_open_proto, 'Open Protocol...\t')
        self.Bind(wx.EVT_MENU, self.on_open_protocol_file, id=self.id_open_proto)
        # JG 2/4
        protoMenu.Append(self.id_open_proto_pcrash, 'Continue Protocol After Savior Crash...\t')
        self.Bind(wx.EVT_MENU, self.on_open_protocol_file_pcrash, id=self.id_open_proto_pcrash)
        #
        protoMenu.Append(self.id_clear_proto, 'Clear Protocol\t')
        self.Bind(wx.EVT_MENU, self.on_clear_protocol, id=self.id_clear_proto)

        # Open a background image
        fileMenu.Append(wx.ID_OPEN, 'Open Background Image...\tCtrl+B')
        self.Bind(wx.EVT_MENU, self.on_open_background_image, id=wx.ID_OPEN)
        #         self.Bind(wx.EVT_MENU,sel)
        fileMenu.Append(wx.ID_SAVE, 'Save Fixation Image...\tCtrl+I')
        self.Bind(wx.EVT_MENU, self.on_save_fixation_image, id=wx.ID_SAVE)
        fileMenu.AppendSeparator()
        fileMenu.Append(wx.ID_PREFERENCES, 'Preferences')
        self.Bind(wx.EVT_MENU, self.on_preferences, id=wx.ID_PREFERENCES)
        fileMenu.Append(wx.ID_EXIT, 'Exit\tCtrl+Q')
        self.Bind(wx.EVT_MENU, self.on_quit, id=wx.ID_EXIT)

        # Toggle on/off
        self.toggleMenu = wx.Menu()
        self.on_toggle = self.toggleMenu.AppendRadioItem(self.id_on_toggle, 'Yes')
        self.Bind(wx.EVT_MENU, self.on_toggle_press, self.on_toggle)
        self.off_toggle = self.toggleMenu.AppendRadioItem(self.id_off_toggle, 'No')
        self.Bind(wx.EVT_MENU, self.on_toggle_press, self.off_toggle)
        targetMenu.AppendSubMenu(self.toggleMenu,'Visible')
        # Alignment
        self.alignMenu = wx.Menu()
        self.off_align = self.alignMenu.AppendRadioItem(self.id_off_align, 'Off')
        self.Bind(wx.EVT_MENU, self.on_align_presss, self.off_align)
        self.on_align = self.alignMenu.AppendRadioItem(self.id_on_align, 'On')
        self.Bind(wx.EVT_MENU, self.on_align_presss, self.on_align)
        targetMenu.AppendSubMenu(self.alignMenu, 'Alignment')
        # Grid
        self.gridMenu = wx.Menu()
        self.off_grid = self.gridMenu.AppendRadioItem(self.id_off_grid, 'Off')
        self.Bind(wx.EVT_MENU, self.on_grid_press, self.off_grid)
        self.on_grid = self.gridMenu.AppendRadioItem(self.id_on_grid, 'On')
        self.Bind(wx.EVT_MENU, self.on_grid_press, self.on_grid)
        targetMenu.AppendSubMenu(self.gridMenu, 'Grid')

        # Compounds the Menu Bar
        self.SetMenuBar(menubar)

    def get_minor_increment(self):
        return self.MINOR_INCREMENT

    def get_major_increment(self):
        return self.MAJOR_INCREMENT



    def get_vertical_fov(self):
        return self.viewpane.get_v_fov()

    def get_horizontal_fov(self):
        return self.viewpane.get_h_fov()

    def on_preferences(self, event):
        prefs_dialog = PreferencesDialog(self,
                                         major_increment=self.get_major_increment(),
                                         minor_increment=self.get_minor_increment())
        retcon = prefs_dialog.ShowModal()

        if retcon == 1:
            prefs = prefs_dialog.get_prefs()
            self.set_major_increment(prefs['major_increment'])
            self.set_minor_increment(prefs['minor_increment'])

    def handle_message(self, evt):
        switchboard = {
            -1: self.on_quit,
            0: self.mark_location,
            1: self.set_FOV
        }
        if evt.get_datatype() in switchboard:
            switchboard.get(evt.get_datatype())(evt.get_data())

    # Toggle target on/off
    def on_toggle_press(self, event):
        if event.Id == self.id_on_toggle:
            self.LCCanvas.show_fixation(True)
        elif event.Id == self.id_off_toggle:
            self.LCCanvas.show_fixation(False)

    # Alignment
    def on_align_presss(self, event):
        pass

    # Grid
    def on_grid_press(self, event):
        if event.Id == self.id_on_grid:
            self.prev_cursor = self.LCCanvas.set_fixation_cursor(4)
            print(str(self.prev_cursor))
        elif event.Id == self.id_off_grid:
            self.LCCanvas.set_fixation_cursor(self.prev_cursor)

    # End of Menu Bar

    def on_rotation_slider(self, rotation):
        self.viewpane.SetBkgrdRotate(rotation)

    def on_mouse_motion(self, event):
        pos = event.GetPosition()

        self.viewpane.set_mouse_loc(pos, self._eyesign)

        if wx.MouseEvent.LeftIsDown(event):
            # Convert to degrees
            self.horz_loc, self.vert_loc = self.viewpane.to_degrees(pos)
            self.update_fixation_location()
        elif wx.MouseEvent.RightIsDown(event) and self.viewpane.get_state() == 1:
            self.viewpane.set_bkgrd_pan(pos)

    def on_left_mouse_button(self, event):
        pos = event.GetPosition()

        self.viewpane.set_mouse_loc(pos, self._eyesign)
        # Convert to degrees
        self.horz_loc, self.vert_loc = self.viewpane.to_degrees(pos)
        self.update_fixation_location()

    # To ensure we capture the initial offset from the origin of the image during a panning movement.
    def on_right_mouse_button(self, event):
        pos = event.GetPosition()
        if event.RightDown():
            self.viewpane.SetMouseOffset(wx.Point2DFromPoint(pos))
        elif event.RightUp():
            self.viewpane.SetMouseOffset(None)

    def on_mouse_wheel(self, event):
        if self.viewpane.get_state() is 1 or self.viewpane.get_state() is 2:
            self.viewpane.SetBkgrdScale(math.copysign(1.0, event.GetWheelRotation()) * .01)

    def on_button_press(self, evt):
        button = evt.GetEventObject()

        # If the user clicked on Select Image
        if button is self.control._iminitpane.selectim:
            self.on_open_background_image(None)
        elif button is self.control._iminitpane.initalign:

            state = self.viewpane.get_state() + 1

            if state == 2:
                self.viewpane.SetPanAnchor()
            elif state == 3:  # If they hit the button after the initialization, restart the process.
                state = 0

            # Update the states in the two panels
            self.control.SetState(state)
            self.viewpane.set_state(state)


        else:
            pass

    def update_fixation_location(self, degrees=None):

        # If you don't pass in degrees as an argument,
        # then assume that we're using whatever the current degrees are.
        if degrees is None:
            degrees = wx.Point2D(self.horz_loc, self.vert_loc)
        else:
            self.horz_loc = degrees.x
            self.vert_loc = degrees.y
        # Update the respective GUIs
        self.viewpane.set_fix_loc_in_deg(degrees)

        self.control.vertcontrol.SetValue(degrees.y)
        self.control.horzcontrol.SetValue(degrees.x)

        x, y = self.degrees_to_screenpix(degrees.x, degrees.y)

        self.LCCanvas.set_fixation_location(wx.Point2D(x, y))

    def set_major_increment(self, increment):
        self.MAJOR_INCREMENT = increment

    def set_minor_increment(self, increment):
        self.MINOR_INCREMENT = increment

    def set_vertical_fov(self, degrees):
        self.viewpane.set_v_fov(degrees)

    def set_horizontal_fov(self, degrees):
        self.viewpane.set_h_fov(degrees)

    def on_save_fixation_image(self, evt=None):
        dialog = wx.FileDialog(self, 'Save Fixation Display as:', "", "", 'PNG Image (*.png)|*.png', wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            locationpath = dialog.GetDirectory()
            locationfname = dialog.GetFilename()
            dialog.Destroy()

            self.viewpane.pane_to_file(locationpath + os.sep + locationfname)

    def on_set_save_protocol_location(self, evt=None):

        # if we are continuing a protocol after a crash just append to the current one
        if self.curr_path == self.protopath_pcrash:
            self._locfileobj = open(self._locationpath + os.sep + self._locationfname, 'a')
            self._locfileobj.close()
            return

        # If no path exists, then prompt for the location before continuing...
        dialog = wx.FileDialog(self, 'Save Location List As:', "", "", 'CSV (Comma delimited)|*.csv', wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            self._locationpath = dialog.GetDirectory()
            self._locationfname = dialog.GetFilename()
            dialog.Destroy()

            result = wx.ID_YES

            if os.path.isfile(self._locationpath + os.sep + self._locationfname):
                md = wx.MessageDialog(self, "Protocol file already exists! Overwrite?", "Protocol file already exists!",
                                      wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
                result = md.ShowModal()

                if result == wx.ID_YES:
                    self._locfileobj = open(self._locationpath + os.sep + self._locationfname, 'w')  # Write the header
                    self._locfileobj.write(
                        "v0.1,Horizontal Location,Vertical Location,Horizontal FOV,Vertical FOV,Eye\n")
                    self._locfileobj.close()
                    # set the file to be saved to as the current path
                    self.curr_path = self._locfileobj
            else:
                print('Woah Nelly')

    def on_open_protocol_file(self, evt=None):

        dialog = wx.FileDialog(self, 'Select protocol file:', self.header_dir, '',
                               'CSV files (*.csv)|*.csv', wx.FD_OPEN)

        if dialog.ShowModal() == wx.ID_OK:
            self.header_dir = dialog.GetDirectory()
            protofname = dialog.GetFilename()
            dialog.Destroy()

            self.protopath = self.header_dir + os.sep + protofname

            result = wx.ID_NO
            if not self.protocolpane.is_protocol_empty():
                md = wx.MessageDialog(self, "Protocol already exists! Overwrite or Append to existing protocol?",
                                      "Protocol already exists!", wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
                md.SetYesNoCancelLabels("Overwrite", "Append", "Cancel")
                result = md.ShowModal()

            if result == wx.ID_YES:
                self.protocolpane.clear_protocol()
                self.viewpane.clear_locations()
                self.curr_path = self.protopath  # set appended protocol to the current path - JG
                self.protocolpane.load_protocol(self.protopath)
            elif result == wx.ID_NO:
                self.curr_path = self.protopath  # set appended protocol to the current path -JG
                self.protocolpane.load_protocol(self.protopath)

    def on_open_protocol_file_pcrash(self, evt=None):

        if self.curr_path == '':
            dialog = wx.FileDialog(self, 'Select protocol file:', self.header_dir, '',
                               'CSV files (*.csv)|*.csv', wx.FD_OPEN)

            if dialog.ShowModal() == wx.ID_OK:
                self.header_dir = dialog.GetDirectory()
                protofname = dialog.GetFilename()
                self._locationpath = dialog.GetDirectory()
                self._locationfname = dialog.GetFilename()
                dialog.Destroy()

                self.protopath_pcrash = self.header_dir + os.sep + protofname

                pcrash_list = self.protocolpane.load_protocol(self.protopath_pcrash)
                if pcrash_list:
                    self.viewpane.Repaint(self, pcrash_list)
                self.curr_path = self.protopath_pcrash
        else:

            # clear protocol to then reload it back in set up as continuing after crash
            self.protocolpane.clear_protocol()
            self.viewpane.clear_locations()

            pcrash_list = self.protocolpane.load_protocol(self.curr_path)
            if pcrash_list:
                self.viewpane.Repaint(self, pcrash_list)


    ##        self.update_protocol(self.vert_loc,self.horz_loc)

    def on_clear_protocol(self, evt=None):
        dlg = wx.MessageDialog(None, 'Are you sure you want to clear the protocol?', 'Clear Protocol',
                               wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.protocolpane.clear_protocol()
            self.viewpane.clear_locations()
            self._locationfname = None
            self.curr_path = ''  # JG

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

            bkgrdim = wx.EmptyBitmap(1, 1)
            bkgrdim.LoadFile(impath, wx.BITMAP_TYPE_ANY)
            self.viewpane.set_bkgrd(bkgrdim)

    def degrees_to_screenpix(self, deghorz, degvert):

        # Converts Degrees to Screen Pixels - X should be POSITIVE going left on screen for OD

        x = -deghorz * self.SCREEN_PPD

        y = -degvert * self.SCREEN_PPD

        return x, y

    def on_keyboard_press(self, event):
        # Allows For Arrow Control Of The Cursor

        if event.GetKeyCode() == wx.WXK_F4:
            evt = MessageEvent(myEVT_RETURN_MESSAGE, -1, 4, "F4")
            wx.PostEvent(self, evt)

        # elif event.GetKeyCode() == wx.WXK_NUMPAD_SUBTRACT:
        #     self.zoom_out(self)

        if self.viewpane.align_on is True:
            self.on_image_alignment(event)
        elif self.viewpane.align_on is False:
            self.on_move_fixation(event)

    def on_image_alignment(self, event):
        if event.ControlDown():  # The image can only be moved if Control is being held down!
            if event.GetKeyCode() == wx.WXK_DOWN:
                self.viewpane.pan_y = self.viewpane.pan_y + self.MINOR_INCREMENT
                self.viewpane.int_Graph()
            elif event.GetKeyCode() == wx.WXK_UP:
                self.viewpane.pan_y = self.viewpane.pan_y - self.MINOR_INCREMENT
                self.viewpane.int_Graph()
            elif event.GetKeyCode() == wx.WXK_LEFT:
                self.viewpane.pan_x = self.viewpane.pan_x - self.MINOR_INCREMENT
                self.viewpane.int_Graph()
            elif event.GetKeyCode() == wx.WXK_RIGHT:
                self.viewpane.pan_x = self.viewpane.pan_x + self.MINOR_INCREMENT
                self.viewpane.int_Graph()
        else:
            self.on_move_fixation(event)
        event.Skip()

    def on_move_fixation(self, event):
        if event.GetKeyCode() == wx.WXK_DOWN:
            if event.ShiftDown():
                self.vert_loc = self.vert_loc - self.MINOR_INCREMENT
                self.update_fixation_location()
            else:
                self.vert_loc = self.vert_loc - self.MAJOR_INCREMENT
                self.update_fixation_location()
        elif event.GetKeyCode() == wx.WXK_UP:
            if event.ShiftDown():
                self.vert_loc = self.vert_loc + self.MINOR_INCREMENT
                self.update_fixation_location()
            else:
                self.vert_loc = self.vert_loc + self.MAJOR_INCREMENT
                self.update_fixation_location()
        elif event.GetKeyCode() == wx.WXK_LEFT:
            if event.ShiftDown():
                self.horz_loc = self.horz_loc - self.MINOR_INCREMENT
                self.update_fixation_location()
            else:
                self.horz_loc = self.horz_loc - self.MAJOR_INCREMENT
                self.update_fixation_location()
        elif event.GetKeyCode() == wx.WXK_RIGHT:
            if event.ShiftDown():
                self.horz_loc = self.horz_loc + self.MINOR_INCREMENT
                self.update_fixation_location()
            else:
                self.horz_loc = self.horz_loc + self.MAJOR_INCREMENT
                self.update_fixation_location()
        else:
            event.Skip()

    def on_eye_select(self, event):
        # Changes Cursor And Location Names Based On on_eye_select Selected cursor
        state = str(self.control.OS.GetValue()) # true if OS radio button checked
        if state == 'True':  # If it is OS, eyesign is -1
            self._eyesign = -1
            self.r_text.SetLabel('T\ne\nm\np\no\nr\na\nl')
            self.l_text.SetLabel(' \n \nN\na\ns\na\nl\n \n')
            self.control.horzcontrol.flip_labels()
            self.tracker = -1
            self.update_fixation_location()
        elif state == 'False':  # If it is OD, eyesign is 1
            self._eyesign = 1
            self.r_text.SetLabel(' \n \nN\na\ns\na\nl\n \n')
            self.l_text.SetLabel('T\ne\nm\np\no\nr\na\nl')
            self.control.horzcontrol.flip_labels()
            self.tracker = 1
            self.update_fixation_location()

    def on_eye_select_list(self, event):
        # Changes Cursor And Location Names Based On on_eye_select Selected cursor
        state = str(self.control.OS.GetValue())  # true if OS radio button checked
        if state == 'True':  # If it is OS, eyesign is -1
            self._eyesign = -1
            self.r_text.SetLabel('T\ne\nm\np\no\nr\na\nl')
            self.l_text.SetLabel(' \n \nN\na\ns\na\nl\n \n')
            if self._eyesign != self.tracker:
                self.control.horzcontrol.flip_labels()
                self.tracker = -1
            self.update_fixation_location()
        elif state == 'False':  # If it is OD, eyesign is 1
            self._eyesign = 1
            self.r_text.SetLabel(' \n \nN\na\ns\na\nl\n \n')
            self.l_text.SetLabel('T\ne\nm\np\no\nr\na\nl')
            if self._eyesign != self.tracker:
                self.control.horzcontrol.flip_labels()
                self.tracker = 1
            self.update_fixation_location()

    def on_minor_step(self, event):
        self.MINOR_INCREMENT = self.control.minorStep.GetValue()
        self.control.horzcontrol.SetIncrement(self.MINOR_INCREMENT)
        self.control.vertcontrol.SetIncrement(self.MINOR_INCREMENT)

    def on_major_step(self, event):
        self.MAJOR_INCREMENT = self.control.majorStep.GetValue()



    def on_vert_spin(self, event):
        # Entering a vertical location value using the subclass
        y_ent = self.control.vertcontrol.GetValue()
        self.vert_loc = round(float(y_ent), 2)
        self.update_fixation_location()

    def on_horz_spin(self, event):
        # Entering a horizontal location value using the subclass
        x_ent = self.control.horzcontrol.GetValue()
        self.horz_loc = round(float(x_ent), 2)
        self.update_fixation_location()

    def mark_location(self, data):

        # Marks the current lcoation of the fixation target, and dumps it to a file
        self.viewpane.mark_location()
        self.update_protocol(self.control.horzcontrol.get_label_value(), self.control.vertcontrol.get_label_value())
        self.save_location(self.control.horzcontrol.get_value(), self.control.vertcontrol.get_value(), str(data))

    def set_FOV(self, fov):
        if fov != -1:
            self.viewpane.set_fov(fov)

    def update_fixation_color(self, penColor, brushColor):
        # This method allows the user to change the color on the LightCrafter DLP.
        self.LCCanvas.set_fixation_color(penColor, brushColor)

    def update_fixation_cursor(self, cursor):
        # This method allows the user to change the cursor type on the LightCrafter DLP.
        self.LCCanvas.set_fixation_cursor(cursor)

    def update_fixation_cursor_size(self, size):
        # This method allows the user to change the cursor size on the LightCrafter DLP.
        self.LCCanvas.set_fixation_size(size)

    def reset_fixation_location(self, event):
        # Reset fixation target Location
        self.horz_loc = 0.0
        self.vert_loc = 0.0

        self.update_fixation_location()

    def update_protocol(self, horzloc, vertloc):
        # Send a query to our protocol pane, marking a new location if there is one or fulfilling a protocol requirement
        self.protocolpane.update_protocol(
            (self.control.horzcontrol.get_label_value(), self.control.vertcontrol.get_label_value()), self._eyesign,
            self.viewpane.get_fov())

    def save_location(self, horzloc, vertloc, vidnum="-1"):

        # Create a file that we will dump all of the relevant information to
        if self._locationfname is None:
            # If it doesn't exist, then prompt for the location before continuing...
            self.on_set_save_protocol_location()

        try:
            self._locfileobj = open(self._locationpath + os.sep + self._locationfname, 'a')
        except IOError:  # If there is an exception, then the file is already open, or is being written to
            if self._locfileobj.closed:
                pass
                ##                print "Failed to open location dump file!"
                return
            else:
                pass
        ##                print "File is already open, continuing..."

        if self._eyesign == -1:
            eye = "OS"
        else:
            eye = "OD"

        print(vidnum)
        self._locfileobj.write(str(vidnum) + "," + str(horzloc) + "," + str(vertloc) + "," +
                               str(self.viewpane.get_h_fov()) + "," + str(self.viewpane.get_v_fov()) +
                               "," + eye + "\n")

        self._locfileobj.close()

    # Saves The Aligned ViewPane
    def save_viewpane(self, event):
        context = wx.ClientDC(self.imagespace)
        memory = wx.MemoryDC()
        x, y = self.imagespace.ClientSize
        bitmap = wx.EmptyBitmap(x, y, wx.ID_ANY)
        memory.SelectObject(bitmap)
        memory.Blit(0, 0, x, y, context, 0, 0)
        memory.SelectObject(wx.NullBitmap)
        wx.InitAllImageHandlers()
        self.filename = ''
        dialog = wx.FileDialog(self, 'Save Aligned ViewPane As:', self.save_image_dir, self.filename, '*.jpeg*',
                               wx.SAVE | wx.FD_OVERWRITE_PROMPT)
        if dialog.ShowModal() == wx.ID_OK:
            self.save_image_dir = dialog.GetDirectory()
            self.filename = dialog.GetFilename()
            dialog.Destroy()
        bitmap.SaveFile(self.filename + '.jpeg', wx.BITMAP_TYPE_JPEG)

    # Exits The Application
    def on_quit(self, event=wx.EVT_CLOSE):

        self.LCCanvas.Destroy()
        self.Destroy()


class MessageEvent(wx.PyCommandEvent):
    """Event to signal that a count value is ready"""

    def __init__(self, etype, eid, datatype=-1, data=-1):
        """Creates the event object"""
        wx.PyCommandEvent.__init__(self, etype, eid)
        self._datatype = datatype
        self._data = data

    def get_datatype(self):
        return self._datatype

    def get_data(self):
        return self._data


# This thread class generically listens to a queue, and passes what it receives to a specified function.
class ConnListener(asyncore.dispatcher):

    def __init__(self, parent):
        asyncore.dispatcher.__init__(self)
        self.thisparent = parent

        self.HOST = 'localhost'
        self.PORT = 1222
        self.buffer = []

        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.bind((self.HOST, self.PORT))
        print("Listening for a careless whisper from a queue thread...")
        self.listen(1)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            QueueListener(self.thisparent, sock=sock)
            print("Incoming connection from " + repr(addr))


class QueueListener(asyncore.dispatcher_with_send):

    def __init__(self, parent=None, sock=None, map=None):
        asyncore.dispatcher.__init__(self, sock, map)
        self.thisparent = parent
        self.out_buffer = b''
        self.thisparent.Bind(EVT_RETURN_MESSAGE, self.handle_return_message)

    def handle_return_message(self, evt):
        # print("Sending!")
        self.send(evt.get_data().encode("utf-8"))

    def handle_read(self):
        try:
            recvmsg = self.recv(32).decode("utf-8")
            # print("Recieved: "+recvmsg)

            list_o_msg = recvmsg.split("!")

            for msg in list_o_msg:
                if msg:
                    # print("Parsing: " + msg)
                    splitmsg = msg.split(";")

                    if len(splitmsg) == 2:
                        evt = MessageEvent(myEVT_MESSAGE, -1, int(splitmsg[0]), splitmsg[1])
                    else:
                        evt = MessageEvent(myEVT_MESSAGE, -1, int(splitmsg[0]), splitmsg[1:])

                    wx.PostEvent(self.thisparent, evt)

                    if int(splitmsg[0]) == -1:
                        self.close()
                        return
        except ConnectionResetError:
            print("Lost connection to the image whisperer!")
            md = wx.MessageDialog(None, "Lost connection to the image whisperer! Protocol list will no longer update.",
                                  "Lost connection to the image whisperer!", wx.ICON_ERROR | wx.OK)
            md.ShowModal()
            return


# Shows The Window
if __name__ == '__main__':
    app = wx.App(redirect=False)
    frame = wxFixationFrame(None)
    frame.Show()
    app.MainLoop()
