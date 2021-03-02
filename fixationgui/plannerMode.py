import paneWidgets
from LocSpin import LocSpin
from wxFixGUI import wxFixationFrame
import wx
from LightCrafter import wxLightCrafterFrame
from controlPanel import ControlPanel

import controlPanel
import wx.lib.agw.floatspin as FS


class PlannerMode(wxFixationFrame):
    """ plannerMode class """

    def __init__(self, parent=None, id=wx.ID_ANY):
        wx.Frame.__init__(self, parent, id, 'Automated Fixation Graphical User Interface')

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
        self.locfileobjname = None
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
        self.initViewPane(self)
        self.initControlPanel(self, 1) #added to wxFixGUI


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
        # adds the control pannel in its correct spot
        horzsizer.Add(self.control, proportion=0, flag=wx.EXPAND)

        self.init_menubar()

        # Displays Main Panel
        self.SetSizerAndFit(horzsizer)
        self.Layout()
        self.Centre()

        # need this line for onquit
        self.LCCanvas = wxLightCrafterFrame()

    def updates(self, fov):
        self.update_protocol(self.control.horzcontrol.get_label_value(), self.control.vertcontrol.get_label_value())
        self.save_location(self.control.horzcontrol.get_value(), self.control.vertcontrol.get_value(), fov)



if __name__ == '__main__':
    app = wx.App(redirect=False)
    frame = PlannerMode()
    frame.Show()
    app.MainLoop()
