import math
import os
import wx
from matplotlib import cm

from ViewPane import ViewPane
import numpy
import cv2
from PIL import Image


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

    def call_set_bkrgd(self, bkgrdim):
        self.imagepane.set_bkgrd(bkgrdim)

    def initSidePane(self, parent):
        self.sidepane = SidePane(parent, self.imagepane, id=wx.ID_ANY)

    def init_menubar(self):

        # Creates Menu Bar
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()

        menubar.Append(fileMenu, 'File')

        # Open a background image
        # fileMenu.Append(wx.ID_OPEN, 'Open Background Image...\tCtrl+B')
        # self.Bind(wx.EVT_MENU, self.on_open_background_image, id=wx.ID_OPEN)

        # Compounds the Menu Bar
        self.SetMenuBar(menubar)

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
    def __init__(self, parent, imagepane, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):
        super(SidePane, self).__init__(parent, id, pos, size, style, name)

        self.SetBackgroundColour('black')
        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        self.quicklabel = wx.StaticText(self, wx.ID_ANY, 'Image Side Panel', style=wx.ALIGN_CENTER)
        self.quicklabel.SetForegroundColour('white')
        self.quicklabel.SetFont(labelFont)

        # self.reslabel = wx.StaticText(self, wx.ID_ANY, 'Image Resolution: ', style=wx.ALIGN_CENTER)
        # self.reslabel.SetForegroundColour('white')
        # self.reslabel.SetFont(labelFont)

        # self.res = wx.StaticText(self, wx.ID_ANY, 'No Image', style=wx.ALIGN_CENTER)
        # self.res.SetForegroundColour('white')
        # self.res.SetFont(labelFont)

        self._zoom = Buttons(self, parent, imagepane, self)

        sizer = wx.GridBagSizer()
        sizer.Add(self.quicklabel, (1, 0), (1, 4), wx.ALIGN_CENTER)
        # sizer.Add(self.reslabel, (4, 0), (1, 4), wx.ALIGN_CENTER)
        # sizer.Add(self.res, (5, 0), (1, 4), wx.ALIGN_CENTER)

        sizer.Add(self._zoom, (7, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)

class Buttons(wx.Panel):

    '''
    classdocs
    '''

    def __init__(self, parent, imagepane, sidepane, rootparent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(-1, -1), style=wx.SIMPLE_BORDER,
                 name='Quick Locations Panel', port=None):
        super(Buttons, self).__init__(parent, id, pos, size, style, name)

        self.header_dir = ""
        self.filename = ""
        self.buttonList = []
        self._rootparent = rootparent
        self.SetBackgroundColour('black')
        self.imagepaneref = imagepane
        self.sidepane = sidepane
        self.tracker = 0
        self.ImageCoords = numpy.empty((0, 2), float)
        self.LiveCoords = numpy.empty((0, 2), float)


        self.__deg_symbol = u'\N{DEGREE SIGN}'

        buttonalignment = wx.ALIGN_CENTER

        # AddImage
        self.AddImage = wx.Button(self, label='Load Background Image', size=(-1, 30))
        self.AddImage.SetBackgroundColour('medium gray')
        self.AddImage.SetForegroundColour('white')
        self.buttonList.append(self.AddImage)

        # Calibration & Select button
        self.Cali = wx.Button(self, label='  Start Image Calibration  ', size=(-1, 30))
        self.Cali.SetBackgroundColour('medium gray')
        self.Cali.SetForegroundColour('white')
        self.buttonList.append(self.Cali)

        # # Zoom
        # self.zoom = wx.Button(self, label='Zoom', size=(-1, 30))
        # self.zoom.SetBackgroundColour('medium gray')
        # self.zoom.SetForegroundColour('white')
        # self.buttonList.append(self.zoom)
        #
        # # Pan
        # self.pan = wx.Button(self, label='Pan', size=(-1, 30))
        # self.pan.SetBackgroundColour('medium gray')
        # self.pan.SetForegroundColour('white')
        # self.buttonList.append(self.pan)
        #
        # # Rotate
        # self.rotate = wx.Button(self, label='Rotate', size=(-1, 30))
        # self.rotate.SetBackgroundColour('medium gray')
        # self.rotate.SetForegroundColour('white')
        # self.buttonList.append(self.rotate)

        # Bind each button to a listener
        for button in self.buttonList:
            button.Bind(wx.EVT_BUTTON, self.OnButton)

        sizer = wx.GridBagSizer()
        sizer.Add(self.AddImage, (0, 0), (1, 0), buttonalignment)
        sizer.Add(self.Cali, (1, 0), (1, 0), buttonalignment)
        # sizer.Add(self.zoom, (2, 0), (1, 0), buttonalignment)
        # sizer.Add(self.pan, (3, 0), (1, 0), buttonalignment)
        # sizer.Add(self.rotate, (4, 0), (1, 0), buttonalignment)

        box = wx.BoxSizer(wx.VERTICAL)  # To make sure it stays centered in the area it is given
        box.Add(sizer, 0, wx.ALIGN_CENTER)

        self.SetSizerAndFit(box)


    def OnButton(self, evt):

        pressed = evt.GetEventObject()
        if pressed == self.AddImage:
            self.on_open_background_image()
        if pressed == self.Cali:
            if self.tracker == 0:
                self.Cali.SetLabel('Select 1st Point on Image')
                self.tracker = self.tracker + 1
                # make sure the matrices are empty
                self.ImageCoords = numpy.empty((0, 2), float)
                self.LiveCoords = numpy.empty((0, 2), float)

            elif self.tracker == 1:
                # coordinates from 1st spot on image
                coordinates = self.imagepaneref.imagepane._fixLoc
                self.ptim1 = numpy.float32(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select Corresponding Point')
                self.tracker = self.tracker + 1

            elif self.tracker == 2:
                # coordinates from 1st corresponding spot on live
                coordinates = self.imagepaneref.imagepane._fixLoc
                self.ptli1 = numpy.float32(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select 2nd Point on Image')
                self.tracker = self.tracker + 1

            elif self.tracker == 3:
                # coordinates from 2nd spot on image
                coordinates = self.imagepaneref.imagepane._fixLoc
                self.ptim2 = numpy.float32(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select Corresponding Point')
                self.tracker = self.tracker + 1

            elif self.tracker == 4:
                # coordinates from 2nd corresponding spot on live
                coordinates = self.imagepaneref.imagepane._fixLoc
                self.ptli2 = numpy.float32(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select 3rd Point on Image')
                self.tracker = self.tracker + 1

            elif self.tracker == 5:
                # coordinates from 3rd spot on image
                coordinates = self.imagepaneref.imagepane._fixLoc
                self.ptim3 = numpy.float32(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Select Corresponding Point')
                self.tracker = self.tracker + 1

            elif self.tracker == 6:
                # coordinates from 3rd corresponding spot on live
                coordinates = self.imagepaneref.imagepane._fixLoc
                self.ptli3 = numpy.float32(coordinates)

                # change button label for next point
                self.Cali.SetLabel('Calibrate')
                self.tracker = self.tracker + 1

            elif self.tracker == 7:
                # Putting all the coordinates together
                self.ptsim = numpy.float32([self.ptim1, self.ptim2, self.ptim3])
                self.ptsli = numpy.float32([self.ptli1, self.ptli2, self.ptli3])

                # The Affine Transformation
                self.matrix = cv2.getAffineTransform(self.ptsim, self.ptsli)
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
                self.imagepaneref.call_set_bkrgd(self.bkgrdim)

                # change button label
                self.Cali.SetLabel('New Calibration')
                self.tracker = 0

                # delete the temporary file we made
                os.remove(filename)

        # if pressed == self.zoom:
        #     print("Hello")
        #     wx.Bitmap.SetSize(self.bkgrdim, (512, 512))
        # if pressed == self.pan:
        #     print("How are you?")
        # if pressed == self.rotate:
        #     print("Bomb diggity")

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
            # JG affine transformation attempt
            self.img = cv2.imread(impath)
            self.rows, self.cols, self.ch = self.img.shape

            self.imagepaneref.call_set_bkrgd(self.bkgrdim)
            #self.imagepaneref.set_bkgrd(self.bkgrdim)

            # dlg = wx.TextEntryDialog(self, 'Image Scale X Dimension:', 'Image Scale')
            # if dlg.ShowModal() == wx.ID_OK:
            #     self.xdim = dlg.GetValue()
            # dlg.Destroy()
            # print('x dimension is: ', int(self.xdim))
            #
            # dlg = wx.TextEntryDialog(self, 'Image Scale Y Dimension:', 'Image Scale')
            # if dlg.ShowModal() == wx.ID_OK:
            #     self.ydim = dlg.GetValue()
            # dlg.Destroy()
            # print('y dimension is: ', int(self.ydim))
            #
            # # make a string out of the resolution dimensions
            # resolution = str(self.xdim) + ' x ' + str(self.ydim)
            # # reset the res label from No Image to the resolution that was entered
            # print(hex(id(self.resref)))
            # self.sidepane.res.SetLabel(resolution)



if __name__ == '__main__':
    app = wx.App(redirect=False)
    frame = wxImageFrame(None)
    frame.Show()
    app.MainLoop()
