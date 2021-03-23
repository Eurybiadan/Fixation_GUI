import math
import os
import wx
from ViewPane import ViewPane


class wxImageFrame(wx.Frame):

    SCREEN_PPD = 20
    # The increment steps we'll use.
    MINOR_INCREMENT = 0.5
    MAJOR_INCREMENT = 1

    def __init__(self, parent = None, id = wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, 'Test GUI for loading in Images')

        # Initial Conditions
        self.header_dir = ""
        self.filename = ""
        self.text = ""
        self._eyesign = -1
        self.horz_loc = 0.0
        self.vert_loc = 0.0

        self.initImagePane(self)
        self.initSidePane(self)

        horzsizer = wx.BoxSizer(wx.HORIZONTAL)

        horzsizer.Add(self.imagespace, proportion=0, flag=wx.EXPAND)
        horzsizer.Add(self.sidepane, proportion=0, flag=wx.EXPAND)

        self.init_menubar()

        # Displays Main Panel
        self.SetSizerAndFit(horzsizer)
        self.Layout()
        #self.SetClientSize(513, 513)
        self.Centre()

        # Allows Exit Button to Close Serial Communication
        self.Bind(wx.EVT_CLOSE, self.on_quit)

        # Allows For Arrow Keys And Keys In General
        self.Bind(wx.EVT_CHAR_HOOK, self.on_keyboard_press)

        # Handles mouse motion, presses, and wheel motions
        self.imagepane.Bind(wx.EVT_MOTION, self.on_mouse_motion)
        self.imagepane.Bind(wx.EVT_LEFT_DOWN, self.on_left_mouse_button)
        self.imagepane.Bind(wx.EVT_RIGHT_DOWN, self.on_right_mouse_button)
        self.imagepane.Bind(wx.EVT_RIGHT_UP, self.on_right_mouse_button)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_mouse_wheel)

    # Exits The Application
    def on_quit(self, event=wx.EVT_CLOSE):
        self.Destroy()

    def on_keyboard_press(self, event):
        # Allows For Arrow Control Of The Cursor
        self.on_move_fixation(event)

    def initImagePane(self, parent):
        # Set up the Pane
        self.imagespace = wx.Panel(parent, wx.ID_ANY)
        self.imagespace.SetBackgroundColour('black')
        self.imagepane = ViewPane(self.imagespace, size=(513, 513))

    def initSidePane(self, parent):
        self.sidepane = SidePane(parent, id=wx.ID_ANY)

    def init_menubar(self):

        # Creates Menu Bar
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()

        menubar.Append(fileMenu, 'File')

        # Open a background image
        fileMenu.Append(wx.ID_OPEN, 'Open Background Image...\tCtrl+B')
        self.Bind(wx.EVT_MENU, self.on_open_background_image, id=wx.ID_OPEN)

        # Compounds the Menu Bar
        self.SetMenuBar(menubar)

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

            bkgrdim = wx.Bitmap(1, 1)
            bkgrdim.LoadFile(impath, wx.BITMAP_TYPE_ANY)
            self.imagepane.set_bkgrd(bkgrdim)

            dlg = wx.TextEntryDialog(self, 'Image Scale X Dimension:', 'Image Scale')
            if dlg.ShowModal() == wx.ID_OK:
                self.xdim = dlg.GetValue()
            dlg.Destroy()
            print('x dimension is: ', int(self.xdim))

            dlg = wx.TextEntryDialog(self, 'Image Scale Y Dimension:', 'Image Scale')
            if dlg.ShowModal() == wx.ID_OK:
                self.ydim = dlg.GetValue()
            dlg.Destroy()
            print('y dimension is: ', int(self.ydim))

    def on_mouse_motion(self, event):
        pos = event.GetPosition()

        self.imagepane.set_mouse_loc(pos, self._eyesign)

        if wx.MouseEvent.LeftIsDown(event):
            # Convert to degrees
            self.horz_loc, self.vert_loc = self.imagepane.to_degrees(pos)
            self.update_fixation_location()
        elif wx.MouseEvent.RightIsDown(event) and self.imagepane.get_state() == 1:
            self.imagepane.set_bkgrd_pan(pos)

    def on_left_mouse_button(self, event):
        pos = event.GetPosition()

        self.imagepane.set_mouse_loc(pos, self._eyesign)
        # Convert to degrees
        self.horz_loc, self.vert_loc = self.imagepane.to_degrees(pos)
        self.update_fixation_location()

    # To ensure we capture the initial offset from the origin of the image during a panning movement.
    def on_right_mouse_button(self, event):
        pos = event.GetPosition()
        if event.RightDown():
            self.imagepane.SetMouseOffset(wx.Point2DFromPoint(pos))
        elif event.RightUp():
            self.imagepane.SetMouseOffset(None)

    def on_mouse_wheel(self, event):
        if self.imagepane.get_state() is 1 or self.imagepane.get_state() is 2:
            self.imagepane.SetBkgrdScale(math.copysign(1.0, event.GetWheelRotation()) * .01)

    def update_fixation_location(self, degrees=None):

        # If you don't pass in degrees as an argument,
        # then assume that we're using whatever the current degrees are.
        if degrees is None:
            degrees = wx.Point2D(self.horz_loc, self.vert_loc)
        else:
            self.horz_loc = degrees.x
            self.vert_loc = degrees.y
        # Update the respective GUIs
        self.imagepane.set_fix_loc_in_deg(degrees)

        x, y = self.degrees_to_screenpix(degrees.x, degrees.y)

    def degrees_to_screenpix(self, deghorz, degvert):

        # Converts Degrees to Screen Pixels - X should be POSITIVE going left on screen for OD

        x = -deghorz * self.SCREEN_PPD

        y = -degvert * self.SCREEN_PPD

        return x, y

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


class SidePane(wx.Panel):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):
        super(SidePane, self).__init__(parent, id, pos, size, style, name)

        self.SetBackgroundColour('black')
        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        self.quicklabel = wx.StaticText(self, wx.ID_ANY, 'Image Side Panel', style=wx.ALIGN_CENTER)
        self.quicklabel.SetForegroundColour('white')
        self.quicklabel.SetFont(labelFont)

        self.reslabel = wx.StaticText(self, wx.ID_ANY, 'Image Resolution: ', style=wx.ALIGN_CENTER)
        self.reslabel.SetForegroundColour('white')
        self.reslabel.SetFont(labelFont)

        sizer = wx.GridBagSizer()
        sizer.Add(self.quicklabel, (1, 0), (1, 4), wx.ALIGN_CENTER)
        sizer.Add(self.reslabel, (4, 0), (1, 4), wx.ALIGN_CENTER)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

if __name__ == '__main__':
    app = wx.App(redirect=False)
    frame = wxImageFrame(None)
    frame.Show()
    app.MainLoop()
