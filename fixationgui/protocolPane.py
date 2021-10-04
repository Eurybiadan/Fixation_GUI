'''

02-14-2014

@author Robert F Cooper

'''
import os
from decimal import Decimal

import numpy as np
import wx
import csv
import re
import pdfrw
import string

from easygui import multenterbox


ANNOT_KEY = '/Annots'
ANNOT_FIELD_KEY = '/T'
ANNOT_VAL_KEY = '/V'
ANNOT_RECT_KEY = '/Rect'
SUBTYPE_KEY = '/Subtype'
WIDGET_SUBTYPE_KEY = '/Widget'

class ProtocolPane(wx.Panel):
    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.SIMPLE_BORDER, name=''):

        super(ProtocolPane, self).__init__(parent, id, pos, size, style, name)
        self.Ntype = 0  # default for Regular AO; 1 is VA
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

        # changed from selected to right click to avoid issues with the item activated
        self.list.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.on_listitem_selected)
        self.list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.on_activated)
        print("Bound dat list.")
        vbox2 = wx.BoxSizer(wx.VERTICAL)

        vbox2.Add(self.list, 1)

        self.SetSizer(vbox2)
        vbox2.SetSizeHints(self)

        # Initialize the data structure which will hold the protocol
        self._protocol = list()
        self._plannedProtocol = list()
        self._protocolNotes = list()
    # JG 2/5
        # Initial Previously Marked Locations - stored as a list, each tuple containg the FOV and the location, so (HFOV,VFOV,wx.POINT2D(X,Y))
        self.marked_loc = []
    #
        self.planmode = 0
        self.loadplanmode = 0
        # by default the gui will send FOV values to savior and update FOV when list items are selected
        self.guiSendFOV = 1
        self.pdfcall = 0
        self.locSaved = 0
        self.plannedList = 0
        self.ind = 0

    def loadMessageEvtObjects(self, messageEvent, myEvtRetMsg):

        self.messageEvent = messageEvent
        self.myEvtRetMsg = myEvtRetMsg

    def on_listitem_selected(self, listevt, listentry=0, index=0):
        self.ind = index

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
        # if in plannermode don't want to do this next chunk, if any other mode we want to so we can update the FOV via savior
        if self.planmode != 1:
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

    def on_activated(self, listevt, notactivated=0):
        from datetime import datetime
        import easygui as eg
        return  # added to skip the notes code below to avoid problems while this function does not work -JG 09/22/2021
        if self.planmode == 1:
            return
        if notactivated:
            index = 0
        else:
            index = listevt.GetIndex()
        print(index)
        protoVidNum = self.list.GetItemText(index, 0)
        protoLoc = self.list.GetItemText(index, 1)
        protoFOV = self.list.GetItemText(index, 2)
        protoEye = self.list.GetItemText(index, 3)
        # protocolItem = self._protocol[index]
        # protoVidNum = dict.get(protocolItem, 'videoNumber')
        protoVidNum = int(protoVidNum)
        print(protoVidNum)
        if index < len(self._protocol)-1:
            protocolNotesItem = self._protocolNotes[protoVidNum - 1]
            if self.Ntype == 0:
                self.pFocus = dict.get(protocolNotesItem, 'Focus')
                self.pPMTconf = dict.get(protocolNotesItem, 'PMTconf')
                self.pPMTdir = dict.get(protocolNotesItem, 'PMTdir')
                self.pPMTref = dict.get(protocolNotesItem, 'PMTref')
                self.pPMTvis = dict.get(protocolNotesItem, 'PMTvis')
            else:
                self.pFocus = dict.get(protocolNotesItem, 'Focus')
                self.pPMTconf = dict.get(protocolNotesItem, 'PMTconf')

        msg = "Notes"
        title = "Additional Information"
        if self.Ntype == 0:
            fieldNames = ["Notes", "Focus", "PMT Conf", "PMT Dir", "PMT Ref", "PMT Vis"]
        else:
            fieldNames = ["Time", "Notes", "MAR Guess", "# of Trials", "Converged?", "Converged @?", "Focus", "Conf PMT"]
        fieldValues = []  # we start with blanks for the values
        if len(self._protocolNotes) != 0:
            if protoVidNum < len(self._protocolNotes):
                protocolCurrNotes = self._protocolNotes[protoVidNum]
                if len(protocolCurrNotes) == 0:
                    if index < len(self._protocol)-1:
                        if self.Ntype == 0:
                            fieldValues = ["", self.pFocus, self.pPMTconf, self.pPMTdir, self.pPMTref, self.pPMTvis]
                        else:
                            fieldValues = ["", "", "", "", "", "", self.pFocus, self.pPMTconf]
                else:
                    if self.Ntype == 0:
                        self.cNotes = dict.get(protocolCurrNotes, 'Notes')
                        self.cFocus = dict.get(protocolCurrNotes, 'Focus')
                        self.cPMTconf = dict.get(protocolCurrNotes, 'PMTconf')
                        self.cPMTdir = dict.get(protocolCurrNotes, 'PMTdir')
                        self.cPMTref = dict.get(protocolCurrNotes, 'PMTref')
                        self.cPMTvis = dict.get(protocolCurrNotes, 'PMTvis')
                        fieldValues = [self.cNotes, self.cFocus, self.cPMTconf, self.cPMTdir, self.cPMTref, self.cPMTvis]
                        MyFrame(wx)
                        #fieldValues = eg.multenterbox(msg, title, fieldNames, fieldValues)
                        self._protocolNotes[protoVidNum] = dict(Notes=fieldValues[0], Focus=fieldValues[1], PMTconf=fieldValues[2], PMTdir=fieldValues[3], PMTref=fieldValues[4], PMTvis=fieldValues[5])
                    else:
                        self.cTime = dict.get(protocolCurrNotes, 'Time')
                        self.cNotes = dict.get(protocolCurrNotes, 'Notes')
                        self.cMAR = dict.get(protocolCurrNotes, 'MAR')
                        self.cTrials = dict.get(protocolCurrNotes, 'numTrial')
                        self.cConverged = dict.get(protocolCurrNotes, 'conv')
                        self.cConvAt = dict.get(protocolCurrNotes, 'convAt')
                        self.cFocus = dict.get(protocolCurrNotes, 'Focus')
                        self.cPMTconf = dict.get(protocolCurrNotes, 'PMTconf')
                        fieldValues = [self.cTime, self.cNotes, self.cMAR, self.cTrials, self.cConverged, self.cConvAt, self.cFocus, self.cPMTconf]
                        MyFrame(wx)
                        #fieldValues = eg.multenterbox(msg, title, fieldNames, fieldValues)
                        self._protocolNotes[protoVidNum] = dict(Time=fieldValues[0], Notes=fieldValues[1], MAR=fieldValues[2], numTrial=fieldValues[3], conv=fieldValues[4], convAt=fieldValues[5],
                                                                Focus=fieldValues[6], PMTconf=fieldValues[7])
                    self.pdf(protoVidNum, protoLoc, protoFOV, protoEye, self._protocolNotes[protoVidNum])
                    print("Reply was:", fieldValues)
                    return
        if index < len(self._protocol) - 1:
            if self.Ntype == 0:
                fieldValues = ["", self.pFocus, self.pPMTconf, self.pPMTdir, self.pPMTref, self.pPMTvis]
            else:
                # t = datetime.now().strftime('%H:%M:%S')
                fieldValues = ['', '', '', '', '', '', self.pFocus, self.pPMTconf]
        if self.Ntype == 1:
            if len(self._protocolNotes) == 0:
                # t = datetime.now().strftime('%H:%M:%S')
                fieldValues = ['', '', '', '', '', '', '', '']
        # dlg = wx.TextEntryDialog(self, 'Notes:', 'Focus:', 'PMT:', 'Additional Information')
        self.MyframeRef = MyFrame(None)
        fieldValues = MyFrame(self.MyframeRef)
        #fieldValues = eg.multenterbox(msg, title, fieldNames, fieldValues)
        print("Reply was:", fieldValues)

        if self.Ntype == 0:
            newNotesEntry = dict(Notes=fieldValues[0], Focus=fieldValues[1], PMTconf=fieldValues[2], PMTdir=fieldValues[3], PMTref=fieldValues[4], PMTvis=fieldValues[5])
        else:
            newNotesEntry = dict(Time=fieldValues[0], Notes=fieldValues[1], MAR=fieldValues[2],
                                                    numTrial=fieldValues[3], conv=fieldValues[4], convAt=fieldValues[5],
                                                    Focus=fieldValues[6], PMTconf=fieldValues[7])
        self._protocolNotes.append(newNotesEntry)
        self.pdf(protoVidNum, protoLoc, protoFOV, protoEye, newNotesEntry)
        print(newNotesEntry)

    def pdf(self, vidNum, protoLoc, protoFOV, protoEye, entry):
        if self.pdfcall == 1:
            pdf_template = self._Noteslocationpath
        else:
            pdf_template = "AOSLO_Electronic_Notes_Template_v1.pdf"
            if self.locSaved == 0:
                self.savepdfas()
            self.pdfcall = 1
        pdf_output = self._Noteslocationpath
        template_pdf = pdfrw.PdfReader(pdf_template)

        for page in template_pdf.pages:
            annotations = page[ANNOT_KEY]
            for annotation in annotations:
                if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                    if annotation[ANNOT_FIELD_KEY]:
                        key = annotation[ANNOT_FIELD_KEY][1:-1]
                        # print(key)

        eye = str(vidNum)
        FOV = 'FOV ' + str(vidNum)
        locNotes = 'Location  Notes' + str(vidNum)
        focus = 'Focus ' + str(vidNum)
        conf = 'Conf' + str(vidNum)
        dir = 'Dir' + str(vidNum)
        ref = 'Ref' + str(vidNum)
        vis = 'Vis' + str(vidNum)

        data_dict = {
            eye: protoEye,
            FOV: protoFOV,
            locNotes: protoLoc + '; ' + entry.get('Notes'),
            focus: entry.get('Focus'),
            conf: entry.get('PMTconf'),
            dir: entry.get('PMTdir'),
            ref: entry.get('PMTref'),
            vis: entry.get('PMTvis')
        }

        self.fill_pdf(pdf_template, pdf_output, data_dict)

    def savepdfas(self):
        dialog = wx.FileDialog(self, 'Save Notes As:', "", "", 'PDF|*.pdf', wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            self._Noteslocationpath = dialog.GetDirectory()
            self._Noteslocationfname = dialog.GetFilename()

            result = wx.ID_YES

            if os.path.isfile(self._Noteslocationpath + os.sep + self._Noteslocationfname):
                md = wx.MessageDialog(self, "Notes file already exists! Overwrite?",
                                      "Notes file already exists!",
                                      wx.ICON_QUESTION | wx.YES_NO | wx.CANCEL)
                result = md.ShowModal()

                if result == wx.ID_YES:
                    self._Noteslocationpath = self._Noteslocationpath + os.sep + self._Noteslocationfname
                    dialog.Destroy()
                    self.locSaved = 1
                    return
                else:
                    return

            if result == wx.ID_YES:
                self._Noteslocationpath = self._Noteslocationpath + os.sep + self._Noteslocationfname
                dialog.Destroy()
                self.locSaved = 1
                return
            else:
                print('Woah Nelly, something went wrong')

    def fill_pdf(self, input_pdf_path, output_pdf_path, data_dict):
        template_pdf = pdfrw.PdfReader(input_pdf_path)
        for page in template_pdf.pages:
            annotations = page[ANNOT_KEY]
            for annotation in annotations:
                if annotation[SUBTYPE_KEY] == WIDGET_SUBTYPE_KEY:
                    if annotation[ANNOT_FIELD_KEY]:
                        key = annotation[ANNOT_FIELD_KEY][1:-1]
                        if key in data_dict.keys():
                            if type(data_dict[key]) == bool:
                                if data_dict[key] == True:
                                    annotation.update(pdfrw.PdfDict(
                                        AS=pdfrw.PdfName('Yes')))
                            else:
                                annotation.update(
                                    pdfrw.PdfDict(V='{}'.format(data_dict[key]))
                                )
                                annotation.update(pdfrw.PdfDict(AP=''))
        template_pdf.Root.AcroForm.update(pdfrw.PdfDict(NeedAppearances=pdfrw.PdfObject('true')))
        pdfrw.PdfWriter().write(output_pdf_path, template_pdf)

    def notesType(self, type):
        self.Ntype = type


    def load_protocol(self, path, loadplanmode=0):
        self.plannedList = 0
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

                    #self._protocol.append(newentry)
                    self._plannedProtocol.append(newentry)
                    self.plannedList = self.plannedList + 1

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

        for item in self._plannedProtocol:
            ind = self.list.GetItemCount()

            self.list.InsertItem(ind, str(item['videoNumber']))
            self.list.SetItem(ind, 1, item['loc'][0] + ', ' + item['loc'][1])
            self.list.SetItem(ind, 2,
                              str(item['fov'][0]) + self._degree_sign + 'x ' + str(item['fov'][1]) + self._degree_sign)
            self.list.SetItem(ind, 3, item['eye'])
            self.list.SetItemBackgroundColour(ind, (0, 102, 102))

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
            for item in self._plannedProtocol:
                fovitem = dict.get(item, 'fov')
                fovx = '{:.2f}'.format(round(float(fovitem[0]), 2))
                fovy = '{:.2f}'.format(round(float(fovitem[1]), 2))
                fovitem = (fovx, fovy)

                locitem = dict.get(item, 'loc')
                locxsplit = locitem[0].split(' ')
                locx = '{:.2f}'.format(round(float(locxsplit[0]), 2))  # this line
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
                    itemtext = self.list.GetItemText(self.ind, 0)
                    self.list.SetItem(self.ind, 0, str(int(vidnum)))
                    self.list.SetItemBackgroundColour(self.ind, (0, 0, 0))
                    exist = True
                    break


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
            self.on_activated(0, 1)

        return 0

    def updateFOVtoggle(self, fovtoggle):
        self.guiSendFOV = fovtoggle


class MyFrame(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, -1, "Additional Information",size=(475,400))
        self.panel = wx.Panel(self, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)

    def popup(self):

        self.lblTitle = wx.StaticText(self.panel, label="Notes", pos=(240, 25))

        self.lblNotes = wx.StaticText(self.panel, label="Notes", pos=(40, 60))
        self.notes = wx.TextCtrl(self.panel, value="", pos=(110, 60), size=(300, -1))
        self.lblFocus = wx.StaticText(self.panel, label="Focus", pos=(40, 100))
        self.focus = wx.TextCtrl(self.panel, value="", pos=(110, 100), size=(300, -1))
        self.lblConf = wx.StaticText(self.panel, label="PMT Conf", pos=(40, 140))
        self.conf = wx.TextCtrl(self.panel, value="", pos=(110, 140), size=(300, -1))
        self.lblDir = wx.StaticText(self.panel, label="PMT Dir", pos=(40, 180))
        self.dir = wx.TextCtrl(self.panel, value="", pos=(110, 180), size=(300, -1))
        self.lblRef = wx.StaticText(self.panel, label="PMT Ref", pos=(40, 220))
        self.ref = wx.TextCtrl(self.panel, value="", pos=(110, 220), size=(300, -1))
        self.lblVis = wx.StaticText(self.panel, label="PMT Vis", pos=(40, 260))
        self.vis = wx.TextCtrl(self.panel, value="", pos=(110, 260), size=(300, -1))
        self.saveButton = wx.Button(self.panel, label="Okay", pos=(310, 300), size=(100, -1))
        self.closeButton = wx.Button(self.panel, label="Cancel", pos=(110, 300), size=(100, -1))
        self.saveButton.Bind(wx.EVT_BUTTON, self.SaveConnString)
        self.closeButton.Bind(wx.EVT_BUTTON, self.OnQuit)
        self.Bind(wx.EVT_CLOSE, self.OnQuit)
        self.Show()

    def OnQuit(self, event):
        self.Destroy()

    def SaveConnString(self, event):
        self.result_notes = self.notes.GetValue()
        self.result_focus = self.focus.GetValue()
        self.result_conf = self.conf.GetValue()
        self.result_dir = self.dir.GetValue()
        self.result_ref = self.ref.GetValue()
        self.result_vis = self.vis.GetValue()
        self.Destroy()
        print(self.result_notes)
