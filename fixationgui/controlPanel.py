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

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):
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

        oseyesizer.Add(self.OS, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT, 10)
        oseyesizer.Add(os_label, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, 10)
        odeyesizer.Add(self.OD, 0, wx.ALIGN_LEFT | wx.BOTTOM | wx.LEFT, 10)
        odeyesizer.Add(od_label, 0, wx.ALIGN_LEFT | wx.BOTTOM | wx.RIGHT, 10)

        """ FloatSpin Controls """
        # Vertical Floatspin control
        self.vertcontrol = LocSpin(self, wx.ID_ANY, min_val=-20, max_val=20, increment=parent.get_minor_increment(),
                                   value=0, extrastyle=FS.FS_LEFT, poslabel='S', neglabel='I')
        self.vertcontrol.SetFormat('%f')
        self.vertcontrol.SetDigits(1)
        #
        # Horizontal Floatspin control
        self.horzcontrol = LocSpin(self, wx.ID_ANY, min_val=-20, max_val=20, increment=parent.get_minor_increment(),
                                   value=0, extrastyle=FS.FS_LEFT, poslabel='T', neglabel='N')
        self.horzcontrol.SetFormat('%f')
        self.horzcontrol.SetDigits(1)

        """ Cursor tools """
        # Anchor cursor as center
        self.anchorbut = wx.Button(self, label='Center to Cursor', size=(-1, 30))
        self.anchorbut.SetBackgroundColour('medium gray')
        self.anchorbut.SetForegroundColour('white')

        # Reset marked locations
        self.resetlocs = wx.Button(self, label='Reset Locations', size=(-1, 30))
        self.resetlocs.SetBackgroundColour('medium gray')
        self.resetlocs.SetForegroundColour('white')

        """ Initialization Buttons """
        # Image initialization pane
        self._iminitpane = paneWidgets.ImInitPanel(self)

        # Cursor control panel
        self._cursorpane = paneWidgets.CursorPanel(self, parent)

        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(0, 4)
        """ Eye Selection Buttons """
        sizer.Add(eye_label, (0, 0), (1, 4), wx.EXPAND | wx.TOP, 10)
        sizer.Add(oseyesizer, (1, 0), (1, 1), wx.ALIGN_CENTER)
        sizer.Add(odeyesizer, (1, 2), (1, 1), wx.ALIGN_CENTER)
        """ FloatSpin Controls """
        sizer.Add(self.horzcontrol, (2, 0), (1, 2), wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(self.vertcontrol, (2, 2), (1, 2), wx.ALIGN_CENTER | wx.ALL, 5)
        """ Initialization Buttons """
        sizer.Add(self.anchorbut, (3, 0), wx.DefaultSpan, wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(self.resetlocs, (3, 2), wx.DefaultSpan, wx.ALIGN_CENTER | wx.ALL, 5)

        sizer.Add(self._cursorpane, (4, 0), (2, 4), wx.EXPAND, wx.ALL, 5)
        sizer.Add(self._iminitpane, (8, 0), (2, 4), wx.EXPAND, wx.ALL, 5)

        self.SetSizerAndFit(sizer)

    def SetState(self, state):
        self._iminitpane.SetState(state)
        self.Layout()

    def CanAcceptFocusFromKeyboard(self):
        return False

    def CanAcceptFocus(self):  # This forces the things in the panel to be accessed by the mouse only.
        return True
