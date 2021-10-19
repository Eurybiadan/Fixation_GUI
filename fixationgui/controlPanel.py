'''
Created on Aug 28, 2013

@author: Robert F Cooper

'''

import wx
import wx.lib.agw.floatspin as FS

from LocSpin import LocSpin
import paneWidgets


class ControlPanel(wx.Panel):
    '''
    This class encapsulates a Panel which contains all of the control ability for the fixation GUI.
    '''

    def __init__(self, parent, planmode, viewpaneref, fxguiself, protocolref, MessageEvent, myEVT_RETURN_MESSAGE, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):
        '''
        Constructor
        '''
        super(ControlPanel, self).__init__(parent, id, pos, size, style, name)

        self.SetBackgroundColour('black')

        labelFont = wx.Font(11, wx.SWISS, wx.NORMAL, wx.BOLD, False)


        """ Eye Selection Buttons """
        # Eye Label
        eye_label = wx.StaticText(self, wx.ID_ANY, 'EYE', style=wx.ALIGN_CENTER)
        eye_label.SetForegroundColour('white')
        eye_label.SetFont(labelFont)

        # Eye Selection Radiobuttons
        self.OS = wx.RadioButton(self, wx.ID_ANY, label='', size=(-1, -1), style=wx.RB_GROUP)  # Button
        os_label = wx.StaticText(self, wx.ID_ANY, 'OS', size=(-1, -1), style=wx.ALIGN_CENTER)  # Label
        os_label.SetForegroundColour('white')
        os_label.SetFont(labelFont)

        self.OD = wx.RadioButton(self, wx.ID_ANY, label='', size=(-1, -1))  # Button
        od_label = wx.StaticText(self, wx.ID_ANY, 'OD', style=wx.ALIGN_CENTER)  # Label
        od_label.SetForegroundColour('white')
        od_label.SetFont(labelFont)

        oseyesizer = wx.BoxSizer(wx.HORIZONTAL)
        odeyesizer = wx.BoxSizer(wx.HORIZONTAL)

        oseyesizer.Add(self.OS, 0,wx.BOTTOM, 10)
        oseyesizer.Add(os_label, 0, wx.BOTTOM, 10)
        odeyesizer.Add(self.OD, 0, wx.BOTTOM, 10)
        odeyesizer.Add(od_label, 0, wx.BOTTOM, 10)

        """ FloatSpin Controls """
        controlFont = wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD, False)
        # Vertical Floatspin control
        self.vertcontrol = LocSpin(self, wx.ID_ANY, min_val=-20, max_val=20, increment=parent.get_minor_increment(),
                                   value=0, extrastyle=FS.FS_LEFT, poslabel='S', neglabel='I')
        self.vertcontrol.SetFormat('%f')
        self.vertcontrol.SetDigits(2)
        #self.vertcontrol.SetFont(controlFont)
        vert_label = wx.StaticText(self, wx.ID_ANY, 'Vert:', style=wx.ALIGN_RIGHT)  # Label
        vert_label.SetForegroundColour('white')
        vert_label.SetFont(labelFont)
        #
        # Horizontal Floatspin control
        self.horzcontrol = LocSpin(self, wx.ID_ANY, min_val=-20, max_val=20, increment=parent.get_minor_increment(),
                                   value=0, extrastyle=FS.FS_LEFT, poslabel='T', neglabel='N')
        self.horzcontrol.SetFormat('%f')
        self.horzcontrol.SetDigits(2)
        #self.horzcontrol.SetFont(controlFont)
        horz_label = wx.StaticText(self, wx.ID_ANY, 'Horz:', style=wx.ALIGN_RIGHT)  # Label
        horz_label.SetForegroundColour('white')
        horz_label.SetFont(labelFont)

        self.minorStep = wx.lib.agw.floatspin.FloatSpin(self, wx.ID_ANY, min_val=0, max_val=10, increment=0.1, value=parent.get_minor_increment(),
                                                        size=(48,-1), style=FS.FS_LEFT)
        self.minorStep.SetFormat('%f')
        self.minorStep.SetDigits(2)
        minorLabel = wx.StaticText(self, wx.ID_ANY, 'Minor \u0394:', style=wx.ALIGN_RIGHT)  # Label
        minorLabel.SetForegroundColour('white')
        minorLabel.SetFont(labelFont)
        #
        # Horizontal Floatspin control
        self.majorStep = wx.lib.agw.floatspin.FloatSpin(self, wx.ID_ANY, min_val=0, max_val=10, increment=0.1, value=parent.get_major_increment(),
                                                        size=(48,-1), style=FS.FS_LEFT)
        self.majorStep.SetFormat('%f')
        self.majorStep.SetDigits(2)
        # self.horzcontrol.SetFont(controlFont)
        majorLabel = wx.StaticText(self, wx.ID_ANY, 'Major \u0394:', style=wx.ALIGN_RIGHT)  # Label
        majorLabel.SetForegroundColour('white')
        majorLabel.SetFont(labelFont)


        """ Initialization Buttons """
        # Quick Buttons panel
        self._quickpane = paneWidgets.QuickLocationsPanel(self, parent, protocolref)

        # Image initialization pane
        self._iminitpane = paneWidgets.ImInitPanel(self, parent, viewpaneref)

        if planmode is 0:
            # Cursor control panel
            self._cursorpane = paneWidgets.CursorPanel(self, parent)
        else:
            # Added in to create the planning panel buttons -JG
            # Planning panel
            self._planningpane = paneWidgets.PlanningPanel(self, parent, viewpaneref, fxguiself)

        if planmode is 0:
            # AutoAdvance Button
            # Added message things
            self._autoadvance = paneWidgets.AutoAdvance(self, parent, protocolref, MessageEvent, myEVT_RETURN_MESSAGE)

        # QoL Buttons panel
        self._qolpane = paneWidgets.RefButtonsPanel(self, parent)

        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(0, 4)
        """ Eye Selection Buttons """
        sizer.Add(eye_label, (0, 0), (1, 4), wx.EXPAND | wx.TOP, 10)
        sizer.Add(oseyesizer, (1, 0), (1, 2), wx.ALIGN_CENTER)
        sizer.Add(odeyesizer, (1, 2), (1, 2), wx.ALIGN_CENTER)
        """ FloatSpin Controls """
        sizer.Add(horz_label, (2, 0), (1, 1), wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.horzcontrol, (2, 1), (1, 1), wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(vert_label, (2, 2), (1, 1), wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.vertcontrol, (2, 3), (1, 1), wx.ALIGN_CENTER | wx.ALL, 5)

        sizer.Add(minorLabel, (3, 0), (1, 1), wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.minorStep, (3, 1), (1, 1), wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(majorLabel, (3, 2), (1, 1), wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.majorStep, (3, 3), (1, 1), wx.ALIGN_CENTER | wx.ALL, 5)


        sizer.Add(self._quickpane, (4, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)
        if planmode is 0:
            sizer.Add(self._cursorpane, (5, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)
        else:
            sizer.Add(self._planningpane, (5, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)
        sizer.Add(self._iminitpane, (6, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)
        if planmode is 0:
            sizer.Add(self._autoadvance, (7, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)
        sizer.Add(self._qolpane, (8, 0), (1, 4), wx.ALIGN_CENTER | wx.EXPAND)



        self.SetSizerAndFit(sizer)

    def SetState(self, state):
        self._iminitpane.SetState(state)
        self.Layout()

    def CanAcceptFocusFromKeyboard(self):
        return False

    def CanAcceptFocus(self):  # This forces the things in the panel to be accessed by the mouse only.
        return True
