'''

02-14-2014

@author Robert F Cooper

'''
from decimal import Decimal

import numpy as np
import wx
import csv
import re
import string




class ProtocolPane(wx.Panel):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):

        super(ProtocolPane, self).__init__(parent, id, pos, size, style, name)
        self.i = 0
        self.SetBackgroundColour('black')
        self._parent = parent
        self.pattern = re.compile("[ntsiNTIS]")

        self._degree_sign = u'\N{DEGREE SIGN}'

        self.list = wx.ListCtrl(self, style=wx.LC_REPORT, size=(285, -1))
        self.list.SetBackgroundColour('black')
        self.list.SetTextColour((0, 183, 235))
        self.list.InsertColumn(0, 'Video #', format=wx.LIST_FORMAT_CENTER, width=55)
        self.list.InsertColumn(1, 'Location', format=wx.LIST_FORMAT_CENTER, width=80)
        self.list.InsertColumn(2, 'FOV', format=wx.LIST_FORMAT_CENTER, width=75)
        self.list.InsertColumn(3, 'Eye', format=wx.LIST_FORMAT_CENTER, width=30)

        self.list.Bind(wx.EVT_LIST_ITEM_SELECTED, self.on_listitem_selected)
        print("Bound dat list.")
        vbox2 = wx.BoxSizer(wx.VERTICAL)

        vbox2.Add(self.list, 1)

        self.SetSizer(vbox2)
        vbox2.SetSizeHints(self)

        # Initialize the data structure which will hold the protocol
        self._protocol = list()
    # JG 2/5
        # Initial Previously Marked Locations - stored as a list, each tuple containg the FOV and the location, so (HFOV,VFOV,wx.POINT2D(X,Y))
        self.marked_loc = []
    #
        self.planmode = 0
        self.loadplanmode = 0
        # by default the gui will send FOV values to savior and update FOV when list items are selected
        self.guiSendFOV = 1

    def loadMessageEvtObjects(self, messageEvent, myEvtRetMsg):

        self.messageEvent = messageEvent
        self.myEvtRetMsg = myEvtRetMsg

    def on_listitem_selected(self, listevt, listentry=0):

        if listentry:
            eye = dict.get(listentry, 'eye')
            fov = dict.get(listentry, 'fov')
            loc = dict.get(listentry, 'loc')
        else:
            ind = listevt.GetIndex()
            eye = self.list.GetItemText(ind, 3)
            fov = self.list.GetItemText(ind, 2)
            loc = self.list.GetItemText(ind, 1)
        # Unwrap the items:

        # Update the eye first- other values are relative to the eye
        # sets the OS or OD radio button
        self._parent.control.OS.SetValue(eye == "OS")
        self._parent.control.OD.SetValue(eye == "OD")
        self._parent.on_eye_select_list(eye == "OS")

        # This has been put in use properly for planmode -- needed so that the remove button can work properly if item to remove was selected on the list -JG 3/3/2021
        if self.planmode == 1:
            fovtokens = fov.split(self._degree_sign)
            width = float(fovtokens[0])
            height = fovtokens[1]
            height = float(height[2:])
            self._parent.set_horizontal_fov(width)
            self._parent.set_vertical_fov(height)

        # The fov does not get updated here, it sends message to savior who then updates the fov
        # This capability can be toggled on and off from the FOV tab in the menubar
        #if self.loadplanmode == 1:
        if self.guiSendFOV == 1:
            print('protocolpane message values:')
            print(hex(id(self.myEvtRetMsg)))
            print(hex(id(self.messageEvent)))

            # if item on the list is selected
            if listentry:
                fovtokens = fov
                width = float(fovtokens[0])
                height = float(fovtokens[1])
            # if auto advance button is pressed
            else:
                fovtokens = fov.split(self._degree_sign)
                width = float(fovtokens[0])
                height = fovtokens[1]
                height = float(height[2:])
            fovset = str((width, height))
            # need to send width and height to savior.pyw
            evt = self.messageEvent(self.myEvtRetMsg, -1, 4, fovset)
            wx.PostEvent(self, evt)


        # Update the Location.
        if listentry:
            locsplit = loc
        else:
            locsplit = loc.split(',')
        horzsign = 1
        vertsign = 1
        if eye == "OS":  # For OS, Temporal is postive and Nasal is negative.
            horz = locsplit[0]
            if horz[-1] == "N":
                horzsign = -1
            horzval = float(horz[:-1].strip()) * horzsign

            vert = locsplit[1]
            if vert[-1] == "I":
                vertsign = -1
            vertval = float(vert[:-1].strip()) * vertsign

            self._parent.update_fixation_location(wx.Point2D(horzval, vertval))

        elif eye == "OD":  # For OD, Temporal is negative and Nasal is positive.
            horz = locsplit[0]
            if horz[-1] == "T":
                horzsign = -1
            horzval = float(horz[:-1].strip()) * horzsign

            vert = locsplit[1]
            if vert[-1] == "I":
                vertsign = -1
            vertval = float(vert[:-1].strip()) * vertsign

            self._parent.update_fixation_location(wx.Point2D(horzval, vertval))

    def load_protocol(self, path, loadplanmode=0):
        self.loadplanmode = loadplanmode
        with open(path, 'r') as csvfile:
            header = next(csvfile, None)
            header = header.split(',')

            protoreader = csv.reader(csvfile, delimiter=',', quotechar='"')

            #added to clear previous loaded in locations - JG 2/11
            self.marked_loc.clear()

            if header[0].strip() == "v0.1" or header[0].strip() == "v0.2":
                # if the planned mode is set to true (1), then don't read file backwards
                if loadplanmode == 1:
                    rowlist = protoreader
                else:
                    # reversed(list()) used to read in the csv entries backwards to make transition from old to new seamless -JG
                    rowlist = reversed(list(protoreader))
                for row in rowlist:
                    exists = False
                    num_aq = 0
                    self.marked_loc.append((float(row[3]), float(row[4]), wx.Point2D(float(row[1]), float(row[2]))))
                    try:  # Attempt the conversion to direction- if this fails, there are incorrect characters here!
                        if float(row[1]) > 0:
                            if row[5] == "OD":
                                horzloc = str(float(row[1])) + " N"  # switched N and T -JG
                            else:
                                horzloc = str(float(row[1])) + " T"  # switched N and T -JG
                        elif float(row[1]) < 0:
                            if row[5] == "OD":
                                horzloc = str(-float(row[1])) + " T"  # switched N and T added (-) -JG
                            else:
                                horzloc = str(-float(row[1])) + " N"  # switched N and T added (-) -JG
                        else:
                            horzloc = str(float(row[1]))

                        if float(row[2]) > 0:
                            vertloc = str(float(row[2])) + " S"
                        elif float(row[2]) < 0:
                            vertloc = str(-float(row[2])) + " I"  # added (-) -JG
                        else:
                            vertloc = str(float(row[2]))

                    except ValueError:
                        return

                    # to make sure that the video numbers start all as -1 if loadplanmode is 1
                    if loadplanmode:
                        newentry = dict(loc=(horzloc, vertloc),
                                        fov=(row[3], row[4]),
                                        eye=row[5], videoNumber='-1')
                    else:
                        newentry = dict(loc=(horzloc, vertloc),
                                    fov=(row[3], row[4]),
                                    eye=row[5],
                                    videoNumber=row[0])

                    # Commented out since we are using video number and don't want to miss any duplicates
                    # for entry in self._protocol:
                    #     if entry['fov'] == newentry['fov'] and \
                    #             entry['eye'] == newentry['eye'] and \
                    #             entry['loc'] == newentry['loc']:
                    #         exists = True
                    #         break

                    # if not exists:

                    self._protocol.append(newentry)

            self.update_protocol_list()
            return self.marked_loc

    def set_protocol(self, newproto):

        self._protocol = newproto
        self.update_protocol_list()

    def is_protocol_empty(self):
        return not self._protocol

    def clear_protocol(self):
        self._protocol = []
        self.list.DeleteAllItems()
        self.i = 0
        self._parent.set_horizontal_fov(0.1)
        self._parent.set_vertical_fov(0.1)

    def update_protocol_list(self):

        for item in self._protocol:
            ind = self.list.GetItemCount()

            self.list.InsertItem(ind, str(item['videoNumber']))
            self.list.SetItem(ind, 1, item['loc'][0] + ', ' + item['loc'][1])
            self.list.SetItem(ind, 2,
                              str(item['fov'][0]) + self._degree_sign + 'x ' + str(item['fov'][1]) + self._degree_sign)
            self.list.SetItem(ind, 3, item['eye'])
            self.list.SetItemBackgroundColour(ind, (0, 102, 102))

    # This method updates the protocol based on an input set. If the input doesn't match any
    # of the currently loaded protocol, add the new location/settings to the list.
    def update_protocol(self, location, eyesign, curfov, removemode, planmode, viewpaneref, vidnum, locx=0, locy=0):
        self.planmode = planmode
        exist = False

        if eyesign == -1:
            seleye = "OS"
        else:
            seleye = "OD"

        # Condition the location a little bit
        location = (location[0].replace(" ", ""), location[1].replace(" ", ""))

        if removemode is 1:
            entry = dict(num=1, num_obtained=int(1),
                            fov=(curfov[0], curfov[1]), eye=seleye, loc=location)
            fov = dict.get(entry, 'fov')
            eye = dict.get(entry, 'eye')
            loc = dict.get(entry, 'loc')
            i = self._protocol.__len__()-1
            j = 0
            while i >= 0:
                protocolitem = self._protocol[j]
                lfov = dict.get(protocolitem, 'fov')
                leye = dict.get(protocolitem, 'eye')
                lloc = dict.get(protocolitem, 'loc')

                if leye == eye:
                    if lloc == loc:
                        if lfov == fov:
                            self.list.DeleteItem(i)
                            self._protocol.remove(self._protocol[j])
                            viewpaneref.removePast(lfov[0], lfov[1], locx, locy, j)
                            return 0
                j = j+1
                i = i-1
            return 1

        # old logic for Aq #. Checks if video was taken before and adds number to Aq #. Not needed anymore -JG
        # ind = 0
        # for item in self._protocol:
        #     if item['fov'] == curfov and item['eye'] == seleye and item['loc'] == location:
        #         item['num_obtained'] += 1
        #         itemtext = self.list.GetItemText(ind, 0)
        #         self.list.SetItem(ind, 0, str(int(itemtext) + 1))
        #         exist = True
        #         break
        #     else:
        #         ind += 1

        if self.loadplanmode == 1:
            ind = 0
            # checks new locations to be recorded against ones that are in the planned protocol
            # needed to reformat the numbers so they have the correct amount of decimal places to match
            for item in self._protocol:
                fovitem = dict.get(item, 'fov')
                fovx = '{:.2f}'.format(round(float(fovitem[0]), 2))
                fovy = '{:.2f}'.format(round(float(fovitem[1]), 2))
                fovitem = (fovx, fovy)

                locitem = dict.get(item, 'loc')
                locxsplit = locitem[0].split(' ')
                locx = '{:.2f}'.format(round(float(locxsplit[0]), 2))
                if locx != '0.00':
                    locx = locx + locxsplit[1]
                locysplit = locitem[1].split(' ')
                locy = '{:.2f}'.format(round(float(locysplit[0]), 2))
                if locy != '0.00':
                    locy = locy + locysplit[1]
                locitem = (locx, locy)

                curfovitemx = '{:.2f}'.format(round(float(curfov[0]), 2))
                curfovitemy = '{:.2f}'.format(round(float(curfov[1]), 2))
                curfovitem = (curfovitemx, curfovitemy)

                locationitemx = location[0]
                locationitemy = location[1]
                locationitem = (locationitemx, locationitemy)

                if fovitem == curfovitem and item['eye'] == seleye and locitem == locationitem and item['videoNumber'] == '-1':
                    item['videoNumber'] = vidnum
                    itemtext = self.list.GetItemText(ind, 0)
                    self.list.SetItem(ind, 0, str(int(vidnum)))
                    self.list.SetItemBackgroundColour(ind, (0, 0, 0))
                    exist = True
                    break
                else:
                    ind += 1

        if not exist:
            newentry = dict(num=1, videoNumber=vidnum,
                            fov=(curfov[0], curfov[1]), eye=seleye, loc=location)
            self._protocol.append(newentry)

            # If the numbers don't exist, place them at the *top* of the table.
            ind = 0  # self.list.GetItemCount()

            self.list.InsertItem(ind, str(newentry['videoNumber']))
            self.list.SetItem(ind, 1, newentry['loc'][0] + ', ' + newentry['loc'][1])
            self.list.SetItem(ind, 2, str(newentry['fov'][0]) + self._degree_sign + 'x ' + str(
                newentry['fov'][1]) + self._degree_sign)
            self.list.SetItem(ind, 3, newentry['eye'])
            self.list.SetItemBackgroundColour(ind, (0, 0, 0))

        return 0

    def updateFOVtoggle(self, fovtoggle):
        self.guiSendFOV = fovtoggle



