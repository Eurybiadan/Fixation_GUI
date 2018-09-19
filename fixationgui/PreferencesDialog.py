'''
Created on Sept 19, 2018

@author: Robert F Cooper

'''

import wx
from wx.lib.agw.floatspin import FloatSpin


class PreferencesDialog(wx.Dialog):

    def __init__(self, parent, id=-1, title='Preferences', style=wx.DEFAULT_DIALOG_STYLE,
                 major_increment=0.75, minor_increment=0.1):
        super(PreferencesDialog, self).__init__(parent, id, title, (-1, -1), (-1, -1), style)
        self.SetBackgroundColour('black')

        labelFont = wx.Font(10, wx.SWISS, wx.NORMAL, wx.BOLD, False)

        # Spinners for setting the increments
        self.maj_increment_spin = FloatSpin(self, wx.ID_ANY, value=major_increment, digits=2, increment=0.1, size=(65, -1))  # Button
        maj_label = wx.StaticText(self, wx.ID_ANY, 'Major Increment', style=wx.ALIGN_CENTER)  # Label
        maj_label.SetForegroundColour('white')
        maj_label.SetFont(labelFont)

        self.min_increment_spin = FloatSpin(self, wx.ID_ANY, value=minor_increment, digits=2, increment=0.1, size=(65, -1))  # Button
        min_label = wx.StaticText(self, wx.ID_ANY, 'Minor Increment', style=wx.ALIGN_CENTER)  # Label
        min_label.SetForegroundColour('white')
        min_label.SetFont(labelFont)

        # To keep the items properly aligned
        major_increment_sizer = wx.BoxSizer(wx.HORIZONTAL)
        minor_increment_sizer = wx.BoxSizer(wx.HORIZONTAL)

        major_increment_sizer.Add(maj_label, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT, 10)
        major_increment_sizer.AddSpacer(6)
        major_increment_sizer.Add(self.maj_increment_spin, 0,  wx.ALIGN_LEFT | wx.BOTTOM | wx.RIGHT, 10)
        minor_increment_sizer.Add(min_label, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.LEFT, 10)
        minor_increment_sizer.AddSpacer(6)
        minor_increment_sizer.Add(self.min_increment_spin, 0, wx.ALIGN_LEFT | wx.BOTTOM | wx.RIGHT, 10)

        # OK/Cancel bar
        self.ok_button = wx.Button(self, id=wx.OK, label="OK", size=(65,-1))
        self.ok_button.SetBackgroundColour('medium gray')
        self.ok_button.SetForegroundColour('white')
        self.ok_button.Bind(wx.EVT_BUTTON, self.on_okay)

        self.cancel_button = wx.Button(self, id=wx.CANCEL, label="Cancel", size=(65,-1))
        self.cancel_button.SetBackgroundColour('medium gray')
        self.cancel_button.SetForegroundColour('white')
        self.cancel_button.Bind(wx.EVT_BUTTON, self.on_cancel)

        okbar_sizer = wx.BoxSizer(wx.HORIZONTAL)

        okbar_sizer.Add(self.ok_button, 0, wx.ALIGN_LEFT | wx.BOTTOM | wx.LEFT, 2)
        okbar_sizer.AddSpacer(20)
        okbar_sizer.Add(self.cancel_button, 0, wx.ALIGN_RIGHT | wx.BOTTOM | wx.RIGHT, 2)

        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(0, 4)

        sizer.Add(major_increment_sizer, (0, 0), (1, 2), wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(minor_increment_sizer, (1, 0), (1, 2), wx.ALIGN_CENTER | wx.ALL, 5)
        sizer.Add(okbar_sizer, (2, 0), (1, 2), wx.ALIGN_CENTER | wx.ALL, 5)

        self.SetSizerAndFit(sizer)

        self.SetAffirmativeId(wx.OK)
        self.SetEscapeId(wx.CANCEL)
        self.AddMainButtonId(wx.OK)

    def on_okay(self, evt):
        self.EndModal(1)

    def on_cancel(self, evt):
        self.EndModal(-1)

    def get_prefs(self):
        return dict(minor_increment=self.min_increment_spin.GetValue(),
                    major_increment=self.maj_increment_spin.GetValue())
