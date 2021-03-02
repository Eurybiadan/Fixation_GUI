
import wx
import math
from math import fabs
from decimal import *
import numpy as np

# Sets Up The Imaging Space So That It Will Be Automatically Refreshed Using A Double Buffer As The ViewPane And Cursor Location Are Changed

class ViewPane(wx.Window):
    def __init__(self ,parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=(513 ,513), style=0, name='ViewPane'):
        wx.Window.__init__(self ,parent ,id ,pos ,size ,style ,name)
        # Number of Grid Lines
        self._numgridlines =30
        self._pixperdeg =1
        # Initial Values
        self.w = 1
        self.h = 1
        self._center   = wx.Point2D(1 ,1) # Center location of the ViewPane.
        self._fixLoc   = wx.Point2D(1 ,1) # Location of the fixation dot on the ViewPane
        self._mouseLoc = ("(0N,0S)") # Current location of the mouse

        # Variables related to the initialization process
        self._state =0
        self._scale =1
        self._deltascale =0
        self._bkgrd_origin = wx.Point2D(0 ,0)
        self._rotation = 0
        self._pananchor = wx.Point2D(0 ,0)
        self._mouseOffset = None # This holds the offset of the mouse, if any, from the origin

        self.align_on = False

        self.scale_x =math.trunc(float(self.w ) /float(self._numgridlines))
        self.scale_y =math.trunc(float(self.h ) /float(self._numgridlines))
        # Cursor Locations
        # Initial Red Cursor
        self. x =math.trunc(float(self.w ) /2)
        self. y =math.trunc(float(self.h ) /2)
        # Initial Field of View
        self.hfov =0.1
        self.vfov =0.1
        # Initial Previously Marked Locations - stored as a list, each tuple containg the FOV and the location, so (HFOV,VFOV,wx.POINT2D(X,Y))
        self.marked_loc =[]
        self.marked_loc_p =[]
        self.hfovplanned = None
        self.vfovplanned = None
        #print('self.hfovplanned in init is: ', self.hfovplanned)

        # Set up pens we'll use
        self.BLKPEN = wx.Pen(wx.BLACK ,1 ,wx.PENSTYLE_SOLID)
        self.THINORANGEPEN = wx.Pen((255, 79, 0), 1, wx.PENSTYLE_SOLID)
        self.MEDORANGEPEN = wx.Pen((255, 79, 0), 3, wx.PENSTYLE_SOLID)
        self.MEDCYANPEN = wx.Pen((0, 183, 235), 2, wx.PENSTYLE_SOLID)
        self.WHTPEN = wx.Pen(wx.WHITE ,1 ,wx.PENSTYLE_SOLID)

        # Set up brushes we'll use
        self.WHTBRSH_TRANS = wx.Brush(wx.WHITE ,wx.TRANSPARENT)
        self.GRYBRSH = wx.Brush((50 ,50 ,50) ,wx.BRUSHSTYLE_SOLID)

        # Set up font's we'll use
        self.MSEFONT = wx.Font(11 ,wx.SWISS ,wx.FONTSTYLE_NORMAL ,wx.FONTWEIGHT_BOLD ,False)

        # Originally doesn't have an image background.
        self._hasbkgrd = False

        # Initialize Backgrounds and the buffer for double buffering
        self._Bkgrd =wx.Bitmap(1, 1)
        self._CurrentBkgrd =wx.Bitmap(1, 1)
        self._Buffer =wx.Bitmap(1, 1)

        # Performs an onSize to initialize all the size-dependent variables
        self.on_size(None)
        self.set_fix_loc_in_deg(wx.Point2D(0, 0))
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)

        # All Mouse Event Handlers
        self.Bind(wx.EVT_ENTER_WINDOW, self.on_enter)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_exit)
        #print('in ViewPane init')

    def set_fov(self, fov):
        self.hfov, self.vfov = fov
        self.hfovplanned = self.hfov
        self.vfovplanned = self.vfov
        self.Repaint()

    def set_v_fov(self, fov):
        self.vfov = fov
        self.Repaint()

    def set_h_fov(self, fov):
        self.hfov = fov
        self.Repaint()

    def get_v_fov(self):
        return self.vfov

    def get_h_fov(self):
        return self.hfov

    def get_fov(self):
        return self.hfov ,self.vfov

    def mark_location(self):
        self.marked_loc.append((self.hfov ,self.vfov ,self._fixLoc))
        self.Repaint()

    def clear_locations(self):
        self.marked_loc = []
        self.marked_loc_p = []
        self.Repaint()

    def set_bkgrd(self, image):
        self._Bkgrd = image
        self._CurrentBkgrd = image
        self._hasbkgrd = True
        self.Repaint()

    def set_mouse_loc(self, posinpix, eyesign):

        degreehorz ,degreevert = self.to_degrees(posinpix)

        self._mouseLoc = "("

        if degreehorz > 0:
            if eyesign < 0:  # If its 1, then Nasal is to the right
                self._mouseLoc = self._mouseLoc + str(degreehorz )+ " T, "
            else:
                self._mouseLoc = self._mouseLoc + str(degreehorz )+ " N, "
        elif degreehorz < 0:
            if eyesign < 0:  # If its 1, then Nasal is to the right
                self._mouseLoc = self._mouseLoc + str(fabs(degreehorz) )+ " N, "
            else:
                self._mouseLoc = self._mouseLoc + str(fabs(degreehorz) )+ " T, "
        else:
            self._mouseLoc = self._mouseLoc + str(degreehorz )+ ", "

        if degreevert > 0:
            self._mouseLoc = self._mouseLoc + str(degreevert )+ " S)"
        elif degreevert < 0:
            self._mouseLoc = self._mouseLoc + str(fabs(degreevert) )+ " I)"
        else:
            self._mouseLoc = self._mouseLoc + str(degreevert )+ ")"

        # print self._mouseLoc
        self.Repaint()

    def set_fix_loc_in_deg(self, pos):
        # Updates the location of the fixation target, and repaints the window
        # Remember (0,0) is top left corner, so subtract to go up!
        self._fixLoc = wx.Point2D( (self._center.x + (pos. x *self._pixperdeg)) , self._center.y - (pos. y *self._pixperdeg) )
        # print "x: "+str(pos.x)+" y: "+str(pos.y)+ " fixation ("+str(self._fixLoc.x)+","+str(self._fixLoc.y)+")"
        self.Repaint()

    def set_fix_loc_in_pix(self, pos, eyesign):
        # Updates the location of the fixation target, and repaints the window
        # Remember (0,0) is top left corner, so subtract to go up!
        self._fixLoc = wx.Point2D(pos.x , pos.y )
        # print "x: "+str(pos.x)+" y: "+str(pos.y)+ " fixation ("+str(self._fixLoc.x)+","+str(self._fixLoc.y)+")"
        self.Repaint()

    def set_state(self, state):
        self._state = state

    def get_state(self):
        return self._state

    def is_aligning(self):
        if self._state > 0 and self._state < 3:
            return True
        else:
            return False

    def to_degrees(self, pos):
        # If it isn't a Point2D, then upconvert it to one
        if type(pos) is wx.Point:
            pos = wx.Point2D(pos)


        relativepos = wx.Point2D(np.subtract(pos.Get(), self._center.Get()))

        degreehorz = round(relativepos. x /self._pixperdeg, 2)

        if (Decimal(str(degreehorz)) % Decimal('0.2')) == Decimal('0.1'):
            degreehorz += .1
        elif (Decimal(str(degreehorz)) % Decimal('0.2')) == Decimal('-0.1'):
            degreehorz -= .1

        degreevert = round(-relativepos. y /self._pixperdeg, 2) # Flip the sign because positive is superior

        if (Decimal(str(degreevert)) % Decimal('0.2')) == Decimal('0.1'):
            degreevert += .1
        elif (Decimal(str(degreevert)) % Decimal('0.2')) == Decimal('-0.1'):
            degreevert -= .1

        return degreehorz ,degreevert

    def on_size(self, event):
        # Is used whenever the window is resized
        # Get the current allowed size of the Window (that is, this canvas)
        win_w ,win_h =self.GetClientSize()

        # Initialize the second buffer (in the double buffer) for drawing
        self._Buffer =wx.Bitmap(win_w ,win_h)

        self._center = wx.Point2D(win_w /2.0 ,win_h /2.0)

        # ViewPane Scaling
        self.img_xscale =1.0
        self.img_yscale =1.0

        # When the size changes, so will the degrees to pixel conversion
        self._pixperdeg = self.degrees_to_pixels((win_w, win_h), self._numgridlines)

        self.Repaint()

    def AcceptsFocus(self):
        return True

    def on_enter(self, event):
        self.inWindow = True
        event.Skip()

    def on_exit(self, event):
        self.inWindow = False
        event.Skip()

    def on_paint(self, event):
        # Allow For Auto-Refresh
        wx.BufferedPaintDC(self, self._Buffer)

    def degrees_to_pixels(self, sizepixels, degperregion):
        # This method takes in a tuple containing the size to determine the degrees to pix
        # based on the number of degrees over a region
        width  = sizepixels[0]
        height = sizepixels[1] # @TODO: Allow oblong scaling of the _pixperdeg

        # 1 degree box
        return width /degperregion

    def set_bkgrd_pan(self, panxy):
        # We want the user to have the point their mouse is at be the center of the image.
        # So, offset the current point by it position relative to the image's top right corner.
        panxy = wx.Point2D(panxy)

        # If the image hasn't been panned yet, or if it isn't contained in the image
        if not self.IsMOffsetSet():
            self._mouseOffset = wx.Point2D( self._CurrentBkgrd.GetWidth( ) /2, self._CurrentBkgrd.GetHeight( ) /2 )

        self._bkgrd_origin = panxy -self._mouseOffset
        self.UpdateBkgrd()

    def contains(self, pos):
        if pos.x > self._bkgrd_origin.x and pos.y > self._bkgrd_origin.y and pos.x < \
                (self._CurrentBkgrd.GetWidth() + self._bkgrd_origin.x) and pos.y < (
                self._CurrentBkgrd.GetHeight() + self._bkgrd_origin.y):
            return True
        else:
            return False

    def IsMOffsetSet(self):
        if self._mouseOffset is not None:
            return True
        else:
            return False

    def SetMouseOffset(self, pos):  # This allows the user to click and drag on any part of the image to move it.
        if pos is not None and self.contains(pos):
            self._mouseOffset = pos - self._bkgrd_origin
        else:
            self._mouseOffset = None

    def SetPanAnchor(self):
        # Take the current positon of the fixation target, and make it the anchor moving forward with initialization.
        self._pananchor = wx.Point2DCopy(self._fixLoc)

    def SetBkgrdRotate(self, degrees):
        self._rotation = math.pi * degrees / 180  # Convert to radians
        self.UpdateBkgrd()

    def SetBkgrdScale(self, deltascale):
        self._deltascale = deltascale
        self._scale = self._scale + deltascale
        self.UpdateBkgrd()

    def UpdateBkgrd(self):
        # This method handles the various incarnations that the background image goes through

        # Convert it to an image to work on it
        im = self._Bkgrd.ConvertToImage()

        if self._state > 0:  # State 1+ has the background panned/scaled
            # Scale
            im.Rescale(self._Bkgrd.GetWidth() * self._scale, self._Bkgrd.GetHeight() * self._scale,
                       quality=wx.IMAGE_QUALITY_NORMAL)
            # Panning is done upon drawing it into the viewpane.

        if self._state > 1:  # State 2+ has the background rotated
            # Rotate it about its center
            oldloc = self._pananchor - self._bkgrd_origin
            newloc = oldloc * (1 + self._deltascale)
            # print "Pan Anchor"
            # print self._pananchor
            # print "Origin:"
            # print self._bkgrd_origin

            self._bkgrd_origin = self._bkgrd_origin - (newloc - oldloc)
            pass
        if self._state > 2:
            pass

        self._CurrentBkgrd = wx.BitmapFromImage(im)
        self.Repaint()

    def pane_to_file(self, filename):
        self._Buffer.SaveFile(filename, wx.BITMAP_TYPE_BMP)

    def Repaint(self, *args):
        # Create a drawing context, and aim what we do with it at the buffer
        dc = wx.MemoryDC()
        dc.SelectObject(self._Buffer)
        # Draw on the buffer
        if args:
            self.marked_loc_p = args[1]
        self.Paint(dc)
        # Finalize. We have to remove the drawing context from the buffer
        # *before* we move the newly drawn stuff to the bitmap!
        del dc

        self.Refresh(eraseBackground=False)
        self.Update()

    def Colorize(self, var1, var2, gc, *args):
        # Function to set past locations to be drawn in different colors based on the variables passed in
        # Could be used for colorizing quality, overlap, differentiating previous protocols
        # Currently set up for fov size:
        # Yellow = 1, smaller = redder, bigger = greener/bluer -JG 2/4/2021
        if var1 <= 0.5 or var2 <= 0.5:
            gc.SetPen(wx.Pen(wx.Colour(red=255, green=0, blue=0), 2, wx.SOLID))
        elif var1 <= 0.75 or var2 <= 0.75:
            gc.SetPen(wx.Pen(wx.Colour(red=255, green=128, blue=0), 2, wx.SOLID))
        elif var1 <= 1.0 and var2 <= 1.0:
            gc.SetPen(wx.Pen(wx.Colour(red=255, green=255, blue=0), 2, wx.SOLID))
        elif var1 <= 1.25 or var2 <= 1.25:
            gc.SetPen(wx.Pen(wx.Colour(red=0, green=255, blue=0), 2, wx.SOLID))
        elif var1 <= 1.5 or var2 <= 1.5:
            gc.SetPen(wx.Pen(wx.Colour(red=0, green=255, blue=255), 2, wx.SOLID))
        elif var1 <= 1.75 or var2 <= 1.75:
            gc.SetPen(wx.Pen(wx.Colour(red=0, green=128, blue=255), 2, wx.SOLID))
        elif var1 <= 2.0 or var2 <= 2.0:
            gc.SetPen(wx.Pen(wx.Colour(red=0, green=0, blue=255), 2, wx.SOLID))
        else:
            gc.SetPen(wx.Pen(wx.Colour(red=127, green=0, blue=255), 2, wx.SOLID))

    # JG 2/5
    def PaintPast(self, gc):
        # Marks Past Locations
        gc.SetBrush(self.WHTBRSH_TRANS)
        # paint live protocol locations
        for mark in self.marked_loc:
            mwidth, mheight, mloc = mark  # Unpack the tuple, draw it.
            # self.Colorize(mwidth, mheight, gc)  # sets colors for rectangles to be drawn with
            gc.SetPen(wx.Pen(wx.Colour(red=0, green=204, blue=204), 2, wx.SOLID))
            gc.DrawRectangle(mloc.x - (self._pixperdeg * mwidth / 2.0) - .5,
                             mloc.y - (self._pixperdeg * mheight / 2.0) - .5, self._pixperdeg * mwidth,
                             self._pixperdeg * mheight)
        # paint loaded in protocol
        gc.SetPen(wx.Pen(wx.Colour(red=255, green=255, blue=255), 2, wx.SOLID))
        for mark in self.marked_loc_p:
            mwidth, mheight, mloc = mark  # Unpack, draw it.
            # adjust location to point on grid
            mloc = wx.Point2D((self._center.x + (mloc.x * self._pixperdeg)),
                              self._center.y - (mloc.y * self._pixperdeg))
            gc.DrawRectangle(mloc.x - (self._pixperdeg * mwidth / 2.0) - .5,
                             mloc.y - (self._pixperdeg * mheight / 2.0) - .5, self._pixperdeg * mwidth,
                             self._pixperdeg * mheight)

    def Paint(self, dc=None):

        if dc is None:
            dc = wx.MemoryDC()
            dc.SelectObject(self._Buffer)

        # Create a GraphicsContext for the floating point drawing we'll do
        gc = wx.GraphicsContext.Create(dc)
        # Determine the current size of the drawing context
        width, height = dc.GetSize()

        # Draw the background first, regardless of any image.
        dc.SetBrush(self.GRYBRSH)
        dc.DrawRectangle(0, 0, width, height)

        if self._hasbkgrd:
            if self._state > 1:
                gc.Translate(self._pananchor.x, self._pananchor.y)
                gc.Rotate(self._rotation)
                gc.Translate(-self._pananchor.x, -self._pananchor.y)
            gc.DrawBitmap(self._CurrentBkgrd, self._bkgrd_origin.x, self._bkgrd_origin.y, self._CurrentBkgrd.GetWidth(),
                          self._CurrentBkgrd.GetHeight())
            # Destroy this graphicscontext so it doesn't carry over what we did to the rest of the viewpane!
            del gc
            gc = wx.GraphicsContext.Create(dc)

        # Grid
        width, height = dc.GetSize()
        numRows, numCols = self._numgridlines, self._numgridlines
        cellWid = float(width - 1) / numRows
        cellHgt = float(height - 1) / numCols

        dc.SetBrush(self.WHTBRSH_TRANS)
        dc.SetPen(self.WHTPEN)
        dc.SetPen(self.BLKPEN)

        # Draw Row lines
        for rowNum in range(numRows + 1):
            if rowNum == 5 or rowNum == 10 or rowNum == 20 or rowNum == 25:
                dc.SetPen(self.THINORANGEPEN)
            else:
                dc.SetPen(self.BLKPEN)
            dc.DrawLine(0, rowNum * cellHgt, width, rowNum * cellHgt)

        # Draw Column lines
        for colNum in range(numCols + 1):
            if colNum == 5 or colNum == 10 or colNum == 20 or colNum == 25:
                dc.SetPen(self.THINORANGEPEN)
            else:
                dc.SetPen(self.BLKPEN)
            dc.DrawLine(colNum * cellWid, 0, colNum * cellWid, height)

        # Draws Center Lines
        dc.SetPen(self.MEDORANGEPEN)
        dc.DrawLine(0, self._numgridlines / 2 * cellHgt, width, self._numgridlines / 2 * cellHgt)
        dc.DrawLine(self._numgridlines / 2 * cellWid, 0, self._numgridlines / 2 * cellWid, height)

        # Draws Viewable Region Circle - use the graphics context because its actually
        # Got a bit of AA in it (can do floating point drawing)
        brush = gc.CreateBrush(self.WHTBRSH_TRANS)
        pen = gc.CreatePen(self.MEDCYANPEN)

        gc.SetBrush(brush)
        gc.SetPen(pen)
        gc.DrawEllipse(1, 1, width - 2, height - 2)

        # Marks Past Locations
        self.PaintPast(gc)

        fovwidth = self._pixperdeg * self.hfov
        fovheight = self._pixperdeg * self.vfov

        if self.hfovplanned is not None:
            # print('It is not none')
            fovwidth = self._pixperdeg * self.hfovplanned
            fovheight = self._pixperdeg * self.vfovplanned

        gc.SetBrush(wx.Brush(wx.WHITE, wx.TRANSPARENT))

        if self._state > 1 and self._state < 3:
            gc.SetPen(wx.Pen(wx.BLUE, 2, wx.SOLID))
            gc.DrawRectangle(self._pananchor.x - (fovwidth / 2.0) - .5, self._pananchor.y - (fovheight / 2.0) - .5,
                             fovwidth, fovheight)

        # Draws Current fixation box
        gc.SetBrush(wx.Brush(wx.WHITE, wx.TRANSPARENT))
        gc.SetPen(wx.Pen(wx.WHITE, 2, wx.SOLID))

        # Since the Window is fixed at 513x513, the "_center is the _center row/column of pixels at 256.5,256.5
        # This means there are 256 pixels to the left of the _center, and 256 pixels to the right. This can change if overriden by the user.
        gc.DrawRectangle(self._fixLoc.x - (fovwidth / 2.0) - .5, self._fixLoc.y - (fovheight / 2.0) - .5, fovwidth,
                         fovheight)
        dc.SetFont(self.MSEFONT)
        dc.SetTextForeground('white')
        dc.DrawText(self._mouseLoc, 0, 0)

        del gc





