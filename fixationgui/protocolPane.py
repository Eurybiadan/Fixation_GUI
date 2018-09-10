'''

02-14-2014

@author Robert F Cooper

'''

import wx
import csv
import re
import string

class ProtocolPane(wx.Panel):
    def __init__(self,parent,id=-1,pos=wx.DefaultPosition,size=wx.DefaultSize,style=wx.SIMPLE_BORDER,name=''):

        super(ProtocolPane,self).__init__(parent,id,pos,size,style,name)
        self.SetBackgroundColour('black')

        self.pattern = re.compile("[ntsiNTIS]")
        
        
        self.list = wx.ListCtrl(self, style=wx.LC_REPORT,size=(270,-1))
        self.list.SetBackgroundColour('black')
        self.list.SetTextColour((236,118,0))
        self.list.InsertColumn(0, '# Remaining', format=wx.LIST_FORMAT_CENTER, width=80)
        self.list.InsertColumn(1, 'FOV', format=wx.LIST_FORMAT_CENTER, width=60)
        self.list.InsertColumn(2, 'Eye', format=wx.LIST_FORMAT_CENTER, width=30)
        self.list.InsertColumn(3, 'Location', format=wx.LIST_FORMAT_CENTER, width=90)

        vbox2 = wx.BoxSizer(wx.VERTICAL)

        vbox2.Add(self.list, 1)
        
        self.SetSizer(vbox2)
        vbox2.SetSizeHints(self)

        # Initialize the data structure which will hold the protocol
        self._protocol = list()

##        with open('R:\\Rob Cooper\\Fixation_GUI - Subprocess\\test_protocol.csv','rb') as csvfile:
##            protoreader = csv.reader(csvfile, delimiter=',', quotechar='"')
##
##            for row in protoreader:
##
##                # Remove whatever non-number characters are around the value, and force the number to be float
##                horzloc = row[4].replace(" ","")
##                horzdir = self.pattern.findall(horzloc)
##                horzloc = string.strip(horzloc, "ntsiNTIS")
##                
##                vertloc = row[5].replace(" ","")
##                vertdir = self.pattern.findall(vertloc)
##                vertloc = string.strip(vertloc, "ntsiNTIS")
##
##
##                horzdir = ('' if not horzdir else horzdir[0])
##                vertdir = ('' if not vertdir else vertdir[0])
##
##                try: # Attempt the conversion to float- if this fails, there are incorrect characters here!
##                    horzloc = str(float(horzloc)) + horzdir           
##                except ValueError: # HANDLE THIS ERROR
##                    return
##
##                try: # If it is at 0,0, the user may not have set it to 0.0- so convert it to that for comparison
##                    vertloc = str(float(vertloc)) + vertdir
##                except ValueError:
##                    return
##
##                self._protocol.append(dict( num=int(0),
##                                            reqnum=int(row[0]),
##                                            fov=( float( row[1].replace(" ","") ) , # Make sure to strip any spaces the user put in...
##                                                  float( row[2].replace(" ","") ) ),
##                                            eye=row[3],
##                                            loc=(horzloc, vertloc) ))
##                
##        self.UpdateProtocolList()

    def LoadProtocol(self, path):
        with open(path,'rb') as csvfile:
            protoreader = csv.reader(csvfile, delimiter=',', quotechar='"')

            for row in protoreader:

                # Remove whatever non-number characters are around the value, and force the number to be float
                horzloc = row[4].replace(" ","")
                horzdir = self.pattern.findall(horzloc)
                horzloc = string.strip(horzloc, "ntsiNTIS")
                
                vertloc = row[5].replace(" ","")
                vertdir = self.pattern.findall(vertloc)
                vertloc = string.strip(vertloc, "ntsiNTIS")


                horzdir = ('' if not horzdir else horzdir[0])
                vertdir = ('' if not vertdir else vertdir[0])

                try: # Attempt the conversion to float- if this fails, there are incorrect characters here!
                    horzloc = str(float(horzloc)) + horzdir           
                except ValueError: # HANDLE THIS ERROR
                    return

                try: # If it is at 0,0, the user may not have set it to 0.0- so convert it to that for comparison
                    vertloc = str(float(vertloc)) + vertdir
                except ValueError:
                    return

                self._protocol.append(dict( num=int(0),
                                            reqnum=int(row[0]),
                                            fov=( float( row[1].replace(" ","") ) , # Make sure to strip any spaces the user put in...
                                                  float( row[2].replace(" ","") ) ),
                                            eye=row[3],
                                            loc=(horzloc, vertloc) ))
            self.UpdateProtocolList()
        

    def SetProtocol(self, newproto):
        
        self._protocol = newproto
        self.list.UpdateProtocolList()

    def ClearProtocol(self):
        self._protocol = []
        self.list.DeleteAllItems()

    def UpdateProtocolList(self):
        degree_sign =  u'\N{DEGREE SIGN}'

        self.list.DeleteAllItems()

        for item in self._protocol:
            
            ind = self.list.GetItemCount()
            numremain = item['reqnum']-item['num']
##            print item
            if numremain < 0:
                remaincolor = round(255.0)
            else:
                remaincolor = round(item['num']*255.0/item['reqnum'])
            
            self.list.InsertStringItem( ind,    str(numremain))
            self.list.SetStringItem(ind, 1, str(item['fov'][0])+degree_sign+ 'x ' + str(item['fov'][1])+degree_sign)
            self.list.SetStringItem(ind, 2, item['eye'])
            self.list.SetStringItem(ind, 3, item['loc'][0] + ', ' + item['loc'][1] )
            self.list.SetItemBackgroundColour( ind, (remaincolor,remaincolor,remaincolor) )

    # This method updates the protocol based on an input set. If the input doesn't match any
    # of the currently loaded protocol, add the new location/settings to the list.
    def UpdateProtocol(self, location, eyesign, curfov):

        existed = False

        if eyesign == -1:
            seleye = "OS"
        else:
            seleye = "OD"

        # Condition the location a little bit
        location = (location[0].replace(" ",""), location[1].replace(" ",""))

        for item in self._protocol:

            if item['fov'] == curfov and item['eye'] == seleye and item['loc'] == location:

                item['num'] += 1
                existed = True
                break

        if not existed:   
            self._protocol.append(dict( num=1,reqnum=int(0), fov=(curfov[0],curfov[1]), eye=seleye, loc=location ) )

        self.UpdateProtocolList()
