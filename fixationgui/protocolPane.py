'''

02-14-2014

@author Robert F Cooper

'''
import os
from datetime import date

import wx
import csv
import re
import pdfrw


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
        self.count = 0
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
        self.enabled = 1  # notes are enabled by default
        self.popupEN = 1  # popup is enabled by default
        self.quickLocClicked = 0
        self.fixationVisible = 1 # by default since by default is on


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
                fovset = str((1, width, height))
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
        if self.planmode == 1 or self.enabled == 0:
            return
        self.object_notes = Notes(self)  # this is what we will use as 'self' to call notes pop up box - need a new one each time otherwise it will say it was deleted
        if self.quickLocClicked:
            Notes.popup(self.object_notes, self, listevt, notactivated, self.count, self.popupEN, self.quickLocVal)
            self.count = 1
            # self.quickLocClicked = 0
            return
        Notes.popup(self.object_notes, self, listevt, notactivated, self.count, self.popupEN)
        self.count = 1

    def quickLoc(self, button):
        # while button is not 'CTR':
        self.quickLocClicked = 1
        self.quickLocVal = button
        if button == 'CTR':
            self.quickLocClicked = 0


    def pdf(self, vidNum=0, protoLoc=0, protoFOV=0, protoEye=0, entry=0, init=0):
        if self.pdfcall == 1:
            pdf_template = self._Noteslocationpath
        else:
            pdf_template = "AOSLO_Electronic_Notes_Template_v2.pdf"
            if self.locSaved == 0 and init == 0:
                self.savepdfas()
            self.pdfcall = 1
        pdf_output = self._Noteslocationpath
        template_pdf = pdfrw.PdfReader(pdf_template)

        if init:  # this is to save the pdf in the correct folder once you saved location for it
            data_dict = {
                date: date.today()  # doesn't work because the date key for some reason doesn't read, but still need this var so good to have here. Put below for loop below and didn't work etiher
            }
            self.fill_pdf(pdf_template, pdf_output, data_dict)
            return

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
        # print(focus)
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
                    self.pdf(init=1)  # add date save here
                    return
                else:
                    return

            if result == wx.ID_YES:
                self._Noteslocationpath = self._Noteslocationpath + os.sep + self._Noteslocationfname
                dialog.Destroy()
                self.locSaved = 1
                self.pdf(init=1)  # add date save here
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

    def notesEnabled(self, value):
        self.enabled = value

    def popupEnabled(self, value):
        self.popupEN = value


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

    def clear_protocol(self, switch=0):
        self._protocol = []
        self.list.DeleteAllItems()
        self.i = 0
        self._parent.set_horizontal_fov(0.1)
        self._parent.set_vertical_fov(0.1)
        # if switch == 0:  # JG WIP
        #     self.pdfcall = 0
        #     self.count = 0
        #     self._protocolNotes = []

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

    def fixationOn(self, value):
        self.fixationVisible = value

    def updateFOVtoggle(self, fovtoggle):
        self.guiSendFOV = fovtoggle


class Notes(wx.Dialog):
    def __init__(self, parent):  # we will need a reference to the class above to make it all work
        no_sys_menu = wx.CAPTION
        wx.Dialog.__init__(self, parent, -1, "Additional Information",size=(475,400), style=no_sys_menu)

        self.panel = wx.Panel(self, wx.ID_ANY)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.mod = 0

    def popup(self, protocolref, listevt, notactivated, count, popupEN, quickLocValue=0, delete=0):
        self.popup = popupEN
        self.quickLoc = quickLocValue
        if notactivated:
            if count:
                if protocolref.selfArray[0]:
                    protocolref.selfArray[0].Destroy()
                    protocolref.selfArray = [self]
                else:
                    protocolref.selfArray = [self]
            else:
                protocolref.selfArray = [self]
        self.protocolref = protocolref
        self.listevt = listevt
        self.notactivated = notactivated
        self.delete = delete

        if self.notactivated:
            self.index = 0  # will also need another condition of if not activated but part of a planned proto, then index will need to be self.ind - JG 10/5/21
        else:
            self.index = self.listevt.GetIndex()
        # print(self.index)
        self.protoVidNum = self.protocolref.list.GetItemText(self.index, 0)
        self.protoLoc = self.protocolref.list.GetItemText(self.index, 1)
        self.protoFOV = self.protocolref.list.GetItemText(self.index, 2)
        self.protoEye = self.protocolref.list.GetItemText(self.index, 3)
        # protocolItem = self.protocolref._protocol[self.index]
        # self.protoVidNum = dict.get(protocolItem, 'videoNumber')  #JG 6/13/22 going to see if I can use the video number for the index
        self.protoVidNum = int(self.protoVidNum)
        print(self.protoVidNum)
        # if it isn't the top entry in the protocol list (aka the video was just taken)
        if self.index < len(self.protocolref._protocol)-1:
            protocolNotesItem = self.protocolref._protocolNotes[self.protoVidNum - 1]
            self.pFocus = dict.get(protocolNotesItem, 'Focus')
            self.pPMTconf = dict.get(protocolNotesItem, 'PMTconf')
            self.pPMTdir = dict.get(protocolNotesItem, 'PMTdir')
            self.pPMTref = dict.get(protocolNotesItem, 'PMTref')
            self.pPMTvis = dict.get(protocolNotesItem, 'PMTvis')

        # if this isn't the first entry in the notes datastructure
        if len(self.protocolref._protocolNotes) != 0:
            if self.protoVidNum < len(self.protocolref._protocolNotes):  # JG- 11/15/21 need to get around this when switching eyes. Can I change to <=?
                protocolCurrNotes = self.protocolref._protocolNotes[self.protoVidNum]
                if len(protocolCurrNotes) == 0:
                    if self.index < len(self.protocolref._protocol)-1:
                        if protocolref.quickLocClicked:
                            self.Notes = self.quickLoc
                        else:
                            self.Notes = ""
                        self.Focus = self.pFocus
                        self.PMTconf = self.pPMTconf
                        self.PMTdir = self.pPMTdir
                        self.PMTref = self.pPMTref
                        self.PMTvis = self.pPMTvis
                else:
                    self.cNotes = dict.get(protocolCurrNotes, 'Notes')
                    self.cFocus = dict.get(protocolCurrNotes, 'Focus')
                    self.cPMTconf = dict.get(protocolCurrNotes, 'PMTconf')
                    self.cPMTdir = dict.get(protocolCurrNotes, 'PMTdir')
                    self.cPMTref = dict.get(protocolCurrNotes, 'PMTref')
                    self.cPMTvis = dict.get(protocolCurrNotes, 'PMTvis')

                    self.Notes = self.cNotes
                    self.Focus = self.cFocus
                    self.PMTconf = self.cPMTconf
                    self.PMTdir = self.cPMTdir
                    self.PMTref = self.cPMTref
                    self.PMTvis = self.cPMTvis

                    self.mod = 1
                    # if self.popup == 0:
                    #     if self.notactivated:
                    #         self.NoteEntryInit = 1
                    #         self.SaveConnString(1)
                    #     else:
                    #         self.NoteEntryInit = 0
                    # else:
                    self.NotesBox()
                    return

        if self.index < len(self.protocolref._protocol) - 1:
            if protocolref.quickLocClicked:
                self.Notes = self.quickLoc
            else:
                self.Notes = ""
            self.Focus = self.pFocus
            self.PMTconf = self.pPMTconf
            self.PMTdir = self.pPMTdir
            self.PMTref = self.pPMTref
            self.PMTvis = self.pPMTvis

        if len(self.protocolref._protocolNotes) == 0:
            if protocolref.quickLocClicked:
                self.Notes = self.quickLoc
            else:
                self.Notes = ""
            self.Focus = ""
            self.PMTconf = ""
            self.PMTdir = ""
            self.PMTref = ""
            self.PMTvis = ""

        # if self.popup == 0:
        #     if self.notactivated:
        #         self.NoteEntryInit = 1
        #         self.SaveConnString(1)
        #     else:
        #         self.NoteEntryInit = 0
        # else:
        self.NotesBox()

    def NotesBox(self):
        self.lblTitle = wx.StaticText(self.panel, label="Notes", pos=(240, 25))
        self.lblNotes = wx.StaticText(self.panel, label="Notes", pos=(40, 60))
        self.notes = wx.TextCtrl(self.panel, value=self.Notes, pos=(110, 60), size=(300, -1))
        self.lblFocus = wx.StaticText(self.panel, label="Focus", pos=(40, 100))
        self.focus = wx.TextCtrl(self.panel, value=self.Focus, pos=(110, 100), size=(300, -1))
        self.lblConf = wx.StaticText(self.panel, label="PMT Conf", pos=(40, 140))
        self.conf = wx.TextCtrl(self.panel, value=self.PMTconf, pos=(110, 140), size=(300, -1))
        self.lblDir = wx.StaticText(self.panel, label="PMT Dir", pos=(40, 180))
        self.dir = wx.TextCtrl(self.panel, value=self.PMTdir, pos=(110, 180), size=(300, -1))
        self.lblRef = wx.StaticText(self.panel, label="PMT Ref", pos=(40, 220))
        self.ref = wx.TextCtrl(self.panel, value=self.PMTref, pos=(110, 220), size=(300, -1))
        self.lblVis = wx.StaticText(self.panel, label="PMT Vis", pos=(40, 260))
        self.vis = wx.TextCtrl(self.panel, value=self.PMTvis, pos=(110, 260), size=(300, -1))
        self.saveButton = wx.Button(self.panel, label="Okay", pos=(310, 300), size=(100, -1))
        #self.closeButton = wx.Button(self.panel, label="Cancel", pos=(110, 300), size=(100, -1))
        self.saveButton.SetDefault()
        self.Bind(wx.EVT_CHAR_HOOK, self.onKeyPress)
        if self.notactivated:
            self.NoteEntryInit = 1
            self.SaveConnString(1)
        else:
            self.NoteEntryInit = 0
        self.saveButton.Bind(wx.EVT_BUTTON, self.SaveConnString)
        #self.closeButton.Bind(wx.EVT_BUTTON, self.OnQuit)
        #self.Bind(wx.EVT_CLOSE, self.OnQuit)
        if self.popup == 1 or self.notactivated == 0:
            self.Show()



    def OnQuit(self, event):
        self.Destroy()

    def onKeyPress(self, event):
        keyCode = event.GetKeyCode()
        if keyCode == wx.WXK_DOWN:
            i = wx.Window.FindFocus()
            if i == self.notes:
                self.focus.SetFocus()
            if i == self.focus:
                self.conf.SetFocus()
            if i == self.conf:
                self.dir.SetFocus()
            if i == self.dir:
                self.ref.SetFocus()
            if i == self.ref:
                self.vis.SetFocus()
        elif keyCode == wx.WXK_UP:
            i = wx.Window.FindFocus()
            if i == self.focus:
                self.notes.SetFocus()
            if i == self.conf:
                self.focus.SetFocus()
            if i == self.dir:
                self.conf.SetFocus()
            if i == self.ref:
                self.dir.SetFocus()
            if i == self.vis:
                self.ref.SetFocus()
        else:
            event.Skip()

    def SaveConnString(self, event):
        self.result_notes = self.notes.GetValue()
        self.result_focus = self.focus.GetValue()
        self.result_conf = self.conf.GetValue()
        self.result_dir = self.dir.GetValue()
        self.result_ref = self.ref.GetValue()
        self.result_vis = self.vis.GetValue()
        if self.NoteEntryInit == 0:
            self.Destroy()

        if self.mod or self.NoteEntryInit == 0:
            self.protocolref._protocolNotes[self.protoVidNum] = dict(Notes=self.result_notes, Focus=self.result_focus, PMTconf=self.result_conf, PMTdir=self.result_dir, PMTref=self.result_ref, PMTvis=self.result_vis)
            print(self.protocolref._protocolNotes[self.protoVidNum])
            self.protocolref.pdf(self.protoVidNum, self.protoLoc, self.protoFOV, self.protoEye, self.protocolref._protocolNotes[self.protoVidNum])
            self.mod = 0
            return

        newNotesEntry = dict(Notes=self.result_notes, Focus=self.result_focus, PMTconf=self.result_conf, PMTdir=self.result_dir, PMTref=self.result_ref, PMTvis=self.result_vis)
        self.protocolref._protocolNotes.append(newNotesEntry)
        print(newNotesEntry)
        self.protocolref.pdf(self.protoVidNum, self.protoLoc, self.protoFOV, self.protoEye, self.protocolref._protocolNotes[self.protoVidNum])
        self.NoteEntryInit = 0


