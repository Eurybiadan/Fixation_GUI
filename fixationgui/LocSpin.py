'''
Created on Aug 28, 2013

@author: Robert F Cooper

This widget allows the user to "spin" through a range with an optional "center", at which, instead of going negative, switches the label.
This code is based on Andrea Gavana's Floatspin control wxPython implementation from 17 Aug 2011.

'''
import wx
import re
import locale
from math import fabs, ceil, floor
from wx.lib.agw.floatspin import FixedPoint
from decimal import *


class LocSpin(wx.lib.agw.floatspin.FloatSpin):
    '''
    classdocs
    '''

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.Point(-1, -1), size=(65, -1),
                 style=0, value=0.0, min_val=None, max_val=None, increment=1.0,
                 digits=2, extrastyle=2, name='FloatSpin', poslabel='T', neglabel='N'):

        self._poslabel = poslabel
        self._neglabel = neglabel

        super(LocSpin, self).__init__(parent, id, pos, size, style, value,
                                      min_val, max_val, increment, digits,
                                      extrastyle, name)

        self._validkeycode.extend(range(65, 90))  # Expand the acceptable characters for upper case letters

        self._validkeycode.extend(range(97, 122))  # Expand the acceptable characters for lower case letters
        getcontext().prec = 2

    # Override
    def SyncSpinToText(self, send_event=True, force_valid=True):
        """
        Synchronize the underlying `wx.TextCtrl` with `wx.SpinButton`.

        :param `send_event`: ``True`` to send a ``EVT_FLOATSPIN`` event, ``False``
         otherwise;
        :param `force_valid`: ``True`` to force a valid value (i.e. inside the
         provided range), ``False`` otherwise.
        """

        if not self._textctrl:
            return

        curr = self._textctrl.GetValue()

        # Added by Robert Cooper to handle input of a number with a string after it
        postrans = str.maketrans(dict.fromkeys(self._poslabel + "- "))
        negtrans = str.maketrans(dict.fromkeys(self._neglabel + "- "))
        # First determine if there are any letter characters in the string.
        if (re.search('[a-zA-Z]', curr) != None):
            # If there are, check if they're the characters for our positive and negative label
            if curr.find(self._poslabel) != -1:
                curr = curr.translate(postrans)
            elif curr.find(self._neglabel) != -1:
                curr = '-' + curr.translate(negtrans)
        # End addition by Robert Cooper

        curr = curr.strip()
        decimalpt = locale.localeconv()["decimal_point"]
        curr = curr.replace(decimalpt, ".")

        if curr:
            try:
                curr = float(curr)
            except:
                self.SetValue(self._value)
                return

            if force_valid or not self.HasRange() or self.InRange(curr):

                if force_valid and self.HasRange():
                    curr = self.ClampValue(curr)

                if self._value != curr:
                    self.SetValue(curr)

                    if send_event:
                        self.DoSendEvent()

        elif force_valid:
            print("Forcing")
            # textctrl is out of sync, discard and reset
            self.SetValue(self.GetValue())

            # Override

    def SetValue(self, value):
        """
        Sets the L{FloatSpin} value.

        :param `value`: the new value.
        """
        if value > 0:
            ispos = 1
        elif value < 0:
            ispos = -1
            value = fabs(value)
        else:
            value = fabs(value)
            ispos = 0

        if not self._textctrl or not self.InRange(value):
            return

        if self._snapticks and self._increment != 0.0:

            finite, snap_value = self.IsFinite(value)

            if not finite:  # FIXME What To Do About A Failure?

                if (snap_value - floor(snap_value) < ceil(snap_value) - snap_value):
                    value = self._defaultvalue + floor(snap_value) * self._increment
                else:
                    value = self._defaultvalue + ceil(snap_value) * self._increment

        decimalpt = locale.localeconv()["decimal_point"]
        strs = ("%100." + str(self._digits) + self._textformat[1]) % value
        strs = strs.replace(".", decimalpt)
        strs = strs.strip()
        strs = self.ReplaceDoubleZero(strs)

        # Added by Robert F Cooper to allow a label change instead of a positive/negative switch.
        if ispos == 1:
            strs = strs + ' ' + self._poslabel
        elif ispos == -1:
            strs = strs + ' ' + self._neglabel
            value = -value
        else:
            value = 0.0  # Don't add any label if it is 0.

        # Ended addition by Robert F Cooper

        if value is not self._value or strs != self._textctrl.GetValue():
            self._textctrl.SetValue(strs)
            self._textctrl.DiscardEdits()
            self._value = value

    def get_label_value(self):
        return self._textctrl.GetValue()

    def get_value(self):
        return Decimal(round(self._value, 2))

    def set_positive_label(self, label):
        self._poslabel = label

    def set_negative_label(self, label):
        self._neglabel = label

    def flip_labels(self):
        label = self._poslabel
        self._poslabel = self._neglabel
        self._neglabel = label

    # Override so that we don't capture spaces.
    def OnChar(self, event):
        keycode = event.GetKeyCode()
        if keycode != wx.WXK_SPACE:
            super(LocSpin, self).OnChar(event)
        else:
            event.Skip()