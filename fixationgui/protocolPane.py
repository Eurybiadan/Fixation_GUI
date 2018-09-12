'''

02-14-2014

@author Robert F Cooper

'''

import wx
import csv
import re
import string


class ProtocolPane(wx.Panel):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):

        super(ProtocolPane, self).__init__(parent, id, pos, size, style, name)
        self.SetBackgroundColour('black')

        self.pattern = re.compile("[ntsiNTIS]")

        self.list = wx.ListCtrl(self, style=wx.LC_REPORT, size=(285, -1))
        self.list.SetBackgroundColour('black')
        self.list.SetTextColour((0, 183, 235))
        self.list.InsertColumn(0, '# Aq', format=wx.LIST_FORMAT_CENTER, width=40)
        self.list.InsertColumn(1, 'Location', format=wx.LIST_FORMAT_CENTER, width=80)
        self.list.InsertColumn(2, 'FOV', format=wx.LIST_FORMAT_CENTER, width=75)
        self.list.InsertColumn(3, 'Eye', format=wx.LIST_FORMAT_CENTER, width=30)

        vbox2 = wx.BoxSizer(wx.VERTICAL)

        vbox2.Add(self.list, 1)

        self.SetSizer(vbox2)
        vbox2.SetSizeHints(self)

        # Initialize the data structure which will hold the protocol
        self._protocol = list()

    def load_protocol(self, path):
        with open(path, 'r') as csvfile:
            header = next(csvfile, None)
            header = header.split(',')

            protoreader = csv.reader(csvfile, delimiter=',', quotechar='"')

            if header[0].strip() == "v0.1":
                for row in protoreader:
                    exists = False
                    num_aq = 0
                    try: # Attempt the conversion to direction- if this fails, there are incorrect characters here!
                        if float(row[1]) > 0:
                            if row[5] == "OD":
                                horzloc = str(float(row[1])) + " T"
                            else:
                                horzloc = str(float(row[1])) + " N"
                        elif float(row[1]) < 0:
                            if row[5] == "OD":
                                horzloc = str(float(row[1])) + " N"
                            else:
                                horzloc = str(float(row[1])) + " T"
                        else:
                            horzloc = str(float(row[1]))

                        if float(row[2]) > 0:
                            vertloc = str(float(row[2])) + " S"
                        elif float(row[2]) < 0:
                            vertloc = str(float(row[2])) + " I"
                        else:
                            vertloc = str(float(row[2]))

                    except ValueError:
                        return

                    newentry = dict(loc=(horzloc, vertloc),
                                    fov=(row[3], row[4]),
                                    eye=row[5],
                                    num_obtained=int(0))

                    for entry in self._protocol:
                        if entry['fov'] == newentry['fov'] and \
                           entry['eye'] == newentry['eye'] and \
                           entry['loc'] == newentry['loc']:

                            exists = True
                            break

                    if not exists:
                        self._protocol.append(newentry)

            self.update_protocol_list()

    def set_protocol(self, newproto):

        self._protocol = newproto
        self.update_protocol_list()

    def is_protocol_empty(self):
        return not self._protocol

    def clear_protocol(self):
        self._protocol = []
        self.list.DeleteAllItems()

    def update_protocol_list(self):
        degree_sign = u'\N{DEGREE SIGN}'

        for item in self._protocol:

            ind = self.list.GetItemCount()

            self.list.InsertItem(ind, str(item['num_obtained']))
            self.list.SetItem(ind, 1, item['loc'][0] + ', ' + item['loc'][1])
            self.list.SetItem(ind, 2, str(item['fov'][0]) + degree_sign + 'x ' + str(item['fov'][1]) + degree_sign)
            self.list.SetItem(ind, 3, item['eye'])
            self.list.SetItemBackgroundColour(ind, (255, 79, 0))

    # This method updates the protocol based on an input set. If the input doesn't match any
    # of the currently loaded protocol, add the new location/settings to the list.
    def update_protocol(self, location, eyesign, curfov):
        degree_sign = u'\N{DEGREE SIGN}'
        exist = False

        if eyesign == -1:
            seleye = "OS"
        else:
            seleye = "OD"

        # Condition the location a little bit
        location = (location[0].replace(" ", ""), location[1].replace(" ", ""))

        for item in self._protocol:
            if item['fov'] == curfov and item['eye'] == seleye and item['loc'] == location:
                item['num_obtained'] += 1
                exist = True
                break

        if not exist:
            newentry = dict(num=1, num_obtained=int(0),
                            fov=(curfov[0], curfov[1]), eye=seleye, loc=location)
            self._protocol.append(newentry)

            ind = self.list.GetItemCount()

            self.list.InsertItem(ind, str(newentry['num_obtained']))
            self.list.SetItem(ind, 1, newentry['loc'][0] + ', ' + newentry['loc'][1])
            self.list.SetItem(ind, 2, str(newentry['fov'][0]) + degree_sign + 'x ' + str(newentry['fov'][1]) + degree_sign)
            self.list.SetItem(ind, 3, newentry['eye'])
            self.list.SetItemBackgroundColour(ind, (255, 79, 0))
