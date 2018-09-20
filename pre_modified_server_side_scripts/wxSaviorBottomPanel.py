#************************************************
#  Copyright 2010                               *
#  The University of Rochester                  *
#  All Rights Reserved                          *
#                                               *
#  Alfredo Dubra  (adubra@cvs.rochester.edu)    *
#  Zachary Harvey (zgh7255@gmail.com)           *
#                                               *
#  Flaum Eye Institute                          *
#  University of Rochester                      *
#  Rochester NY 14642                           *
#                                               *
#  Copyright 2012                               *
#  Medical College of Wisconsing                *
#  All Rights Reserved                          *
#                                               *
#  Zachary Harvey (zgh7255@gmail.com)           *
#  Alfredo Dubra  (adubra@mcw.edu)              *
#                                               *
#  Eye Institute                                *
#  Medical College of Wisconsing                *
#  Milwaukee WI 53226                           *
#************************************************

# importing Python modules 
import wx, wx.lib.intctrl, wx.lib.buttons, threading, time
# importing the I/O module from Scipy
import scipy.io as sio
import os
import copy
import socket

#importing this for some constants
import MatroxFramegrabber 

class wxSaviorBottomPanel(wx.Panel):

    """Image acquisition control panel
    """
    
    def __init__(self, parent, initial_settings, local_savior_path = '.', matrox_frame_grabber_event_generator = None, top_panel = None):

        """
        """        

        # default constructor using the parent window        
        wx.Panel.__init__(self, parent, -1)

        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())

        if parent.fixQ is not None:
            self.fixQ = parent.fixQ

        # keeping track of the hardware control
        self.matrox_frame_grabber_event_generator = matrox_frame_grabber_event_generator
        if matrox_frame_grabber_event_generator != None:
            
            self.matrox_frame_grabber = matrox_frame_grabber_event_generator.GetEventGenerator()

            # bind the OnStateChange method
            self.matrox_frame_grabber_event_generator.BindWXEvent("state_changed", self.OnStateChanged)

            #  bind the grab finished event so that we can write metadata to file
            self.matrox_frame_grabber_event_generator.BindWXEvent("grab_finished", self.OnGrabFinished)
            
        else:
            self.matrox_frame_grabber = None

        # keep a reference to the top panel to update the user on the status
        self.top_panel = top_panel
            
        # adjusting the size to the parent's client size
        self.SetClientSize(parent.GetClientSize())

        self.n_frames_to_record   = -1
        self.current_movie_number = 0

        # creating the sizer and defining control dimensions
        main_sizer                = wx.GridBagSizer(vgap = 0, hgap = 0)
        border                    = 5
        button_width              = 100
        button_height             = button_width/1.61803399 # golden ratio!
        text_ctrl_width           = 50
        text_ctrl_height          = 20
        text_ctrl_size            = (text_ctrl_width, text_ctrl_height)
        button_size               = (button_width, button_height)
        spacer_height             = 15
        spacer_width              = -1

        buttons_colour            = 'gray'
        
        # initializing the sizer row
        current_row               = 0

        ###################################################################
        #                      creating controls                          #
        ###################################################################

       # stop button ######################################################

        # loading stop icons
        stop_icon          = wx.Bitmap(local_savior_path + '/icons/Pause-Hot-icon 30.png',      wx.BITMAP_TYPE_PNG)
        stop_icon_disabled = wx.Bitmap(local_savior_path + '/icons/Pause-Disabled-icon 30.png', wx.BITMAP_TYPE_PNG)

        # creating the button and setting the pressed and disabled icons       
        self.stop_button   = wx.lib.buttons.GenBitmapButton(self, -1,
                                                            stop_icon,
                                                            size  = button_size,
                                                            style = wx.BORDER_SIMPLE)

        # setting the button background
        self.stop_button.SetBackgroundColour(buttons_colour)

        # setting the bitmap for the disabled state
        self.stop_button.SetBitmapDisabled(stop_icon_disabled)       

        # associating an event to the control       
        self.Bind(wx.EVT_BUTTON, self.OnStopButton, self.stop_button)


       # live button ######################################################

        # loading live icons
        live_icon          = wx.Bitmap(local_savior_path + '/icons/play-normal-blue-dark 30.png',   wx.BITMAP_TYPE_PNG)
        live_icon_pressed  = wx.Bitmap(local_savior_path + '/icons/play-normal-blue-bright 30.png', wx.BITMAP_TYPE_PNG)
        live_icon_disabled = wx.Bitmap(local_savior_path + '/icons/play-normal-gray 30.png',        wx.BITMAP_TYPE_PNG)

        # creating the button and setting the pressed and disabled icons        
        self.live_button   = wx.lib.buttons.GenBitmapToggleButton(self, -1,
                                                                  live_icon,
                                                                  size  = button_size,
                                                                  style = wx.BORDER_SIMPLE)

        # setting the button background
        self.live_button.SetBackgroundColour(buttons_colour)

        # setting the bitmap for the selected (pressed) state
        self.live_button.SetBitmapSelected(live_icon_pressed)

        # setting the bitmap for the disabled state
        self.live_button.SetBitmapDisabled(live_icon_disabled)
               
        # associating an event to the control       
        self.Bind(wx.EVT_BUTTON, self.OnLiveButton, self.live_button)
        
        # adding controls to the sizer
        main_sizer.Add((spacer_width, spacer_height),
                       pos  = (current_row, 0), span   = (3, 1),
                       flag = wx.EXPAND|wx.ALL, border = border)
        current_row  += 1        
        main_sizer.Add(self.stop_button,
                       pos  = (current_row, 1), span   = (3, 1),
                       flag = wx.EXPAND,        border = border)
        main_sizer.Add((spacer_width, spacer_height),
                       pos  = (current_row, 2), span   = (3, 1),
                       flag = wx.EXPAND,        border = border)
        main_sizer.Add(self.live_button,
                       pos  = (current_row, 3), span   = (3, 1),
                       flag = wx.EXPAND,        border = border)
        main_sizer.Add((spacer_width, spacer_height),
                       pos  = (current_row, 4), span   = (3, 1),
                       flag = wx.EXPAND,        border = border)


       # record button ######################################################

        # loading record icons
        record_icon          = wx.Bitmap(local_savior_path + '/icons/Record-Normal-icon 30.png',   wx.BITMAP_TYPE_PNG)
        record_icon_pressed  = wx.Bitmap(local_savior_path + '/icons/Record-Pressed-icon 30.png',  wx.BITMAP_TYPE_PNG)
        record_icon_disabled = wx.Bitmap(local_savior_path + '/icons/Record-Disabled-icon 30.png', wx.BITMAP_TYPE_PNG)

        # creating the button and setting the pressed and disabled icons        
        self.record_button   = wx.lib.buttons.GenBitmapToggleButton(self, -1,
                                                                    record_icon,
                                                                    size  = button_size,
                                                                    style = wx.BORDER_SIMPLE)

        # setting the button background                                      
        self.record_button.SetBackgroundColour(buttons_colour)

        # setting the bitmap for the selected (pressed) state
        self.record_button.SetBitmapSelected(record_icon_pressed)

        # setting the bitmap for the disabled state
        self.record_button.SetBitmapDisabled(record_icon_disabled)

        # associating an event to the control
        self.Bind(wx.EVT_BUTTON, self.OnRecordButton, self.record_button)       

        # adding controls to the sizer
        main_sizer.Add(self.record_button,
                       pos  = (current_row, 5), span   = (3, 1),
                       flag = wx.EXPAND, border = border)
        main_sizer.Add((spacer_width - border, spacer_height),
                       pos  = (current_row, 6), span   = (3, 1),
                       flag = wx.EXPAND,        border = border)

             
        # number of frames ########################################
        text_number_of_frames_to_record = wx.StaticText( self, label = " # frames to record:")
        
        self.n_frames_ctrl              = wx.lib.intctrl.IntCtrl(self,
                                                                 value      = initial_settings['n_frames_to_record'],
                                                                 min        = 1,
                                                                 allow_none = False,
                                                                 style      = wx.TE_RIGHT,
                                                                 size       = text_ctrl_size)

        self.check_box_infinite         = wx.CheckBox(self, -1, "  Infinite  ", style = wx.TE_RIGHT)

        self.Bind(wx.EVT_CHECKBOX, self.OnInfiniteCheckBox, self.check_box_infinite)
 
        # adding controls to the sizer
        main_sizer.Add(text_number_of_frames_to_record,
                       pos  = (current_row, 7),                                                   span   = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.BOTTOM, border = border)
        main_sizer.Add(self.n_frames_ctrl,
                       pos  = (current_row, 8),                                                   span   = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.BOTTOM,  border = border)
        main_sizer.Add(self.check_box_infinite,
                       pos  = (current_row, 9),                                                   span   = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_LEFT|wx.LEFT|wx.RIGHT|wx.BOTTOM,  border = border)

        current_row  += 2

        # movie number ####################################################
        text_movie_number                 = wx.StaticText( self,   label = " Next movie #:")
        
        self.movie_number_ctrl            = wx.lib.intctrl.IntCtrl(self,
                                                                   value      = 0,
                                                                   min        = 0,
                                                                   allow_none = False,
                                                                   style      = wx.TE_RIGHT,
                                                                   size       = text_ctrl_size)

        self.text_last_movie_number_saved = wx.StaticText( self, label = "                 ")

        # adding controls to the sizer
        main_sizer.Add(text_movie_number,
                       pos  = (current_row, 7),                                                span   = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.TOP, border = border)
        main_sizer.Add(self.movie_number_ctrl,
                       pos  = (current_row, 8),                                                span   = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.TOP, border = border)
        main_sizer.Add(self.text_last_movie_number_saved,
                       pos  = (current_row, 9),                                                span   = (1, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.LEFT|wx.RIGHT|wx.TOP, border = border)

        current_row  += 1

        main_sizer.Add((spacer_width, spacer_height),
                       pos  = (current_row, 10),                                              span   = (1, 1),
                       flag = wx.EXPAND|wx.ALL,                                               border = border)


        # making the first and last column growable
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableCol(2)
        main_sizer.AddGrowableCol(4)
        main_sizer.AddGrowableCol(6)
        main_sizer.AddGrowableCol(10)

        main_sizer.AddGrowableRow(0)
        main_sizer.AddGrowableRow(3)

        # setting the controls to the values specified by the initial settings
        self.SetCurrentSettings(initial_settings)
    
        # Fitting the current panel to the needs of the sizer.
        self.SetSizerAndFit(main_sizer)

        self.Bind(wx.EVT_CLOSE, self.OnClose)

        

        # end of constructor ##############################################

    def GetCurrentMovieNumber(self):

        return self.current_movie_number

    def OnClose(self, evt):

        """
        """
        
        # stopping the live and record modes for a healthy exit
        self.OnStopButton(None)
           
        # continue with the normal window closing
        evt.Skip()

    def SetCurrentSettings(self, input_settings):

        """Getting the current settings from a Python dictionary.
        """

        if input_settings.has_key('current_movie_number'):
            self.movie_number_ctrl.SetValue(input_settings['current_movie_number'])

    def GetCurrentSettings(self):

        """Returning the current settings in a Python dictionary.
        """

        output_settings = {'record_fixed_number_of_frames_boolean': not self.check_box_infinite.GetValue(),
                           'n_frames_to_record'                   : self.n_frames_ctrl.GetValue(),
                           'current_movie_number'                 : self.movie_number_ctrl.GetValue() }
        

        return output_settings

    def OnInfiniteCheckBox(self, event = None):

        """
        """

        # disabling the # of frames per movie control
        self.n_frames_ctrl.Enable(not self.check_box_infinite.GetValue())

        if event != None:
        
            event.Skip()

    def OnStateChanged(self, event):
        
        if self.matrox_frame_grabber != None:
            current_state = self.matrox_frame_grabber.GetCurrentState()

            # Update UI depending on what state we are int
            if current_state == MatroxFramegrabber.STOPPED:
                self.record_button.SetValue(False)
                self.live_button.SetValue(False)
                self.n_frames_ctrl.Enable(not self.check_box_infinite.GetValue())
                self.check_box_infinite.Enable()

                # update the top panel
                if self.top_panel != None:
                    self.top_panel.SetCurrentModeIcon('stop')
                
            elif current_state == MatroxFramegrabber.LIVE:
                self.record_button.SetValue(False)
                self.live_button.SetValue(True)
                
                self.n_frames_ctrl.Enable(not self.check_box_infinite.GetValue())
                self.check_box_infinite.Enable()

                # update the top panel
                if self.top_panel != None:
                    self.top_panel.SetCurrentModeIcon('live')
                
            elif current_state == MatroxFramegrabber.RECORDING:

                self.record_button.SetValue(True)
                self.live_button.SetValue(False)
                self.n_frames_ctrl.Enable(False)
                self.check_box_infinite.Enable(False)

                # update the top panel
                if self.top_panel != None:
                    self.top_panel.SetCurrentModeIcon('record')
                
            elif current_state == MatroxFramegrabber.PAUSED:
                self.record_button.SetValue(False)
                self.live_button.SetValue(False)
                self.n_frames_ctrl.Enable(not self.check_box_infinite.GetValue())
                self.check_box_infinite.Enable()

                # update the top panel
                if self.top_panel != None:
                    self.top_panel.SetCurrentModeIcon('stop')
                
            elif current_state == MatroxFramegrabber.PAUSED_RECORDING:
                self.record_button.SetValue(False)
                self.live_button.SetValue(False)
                self.n_frames_ctrl.Enable(False)
                self.check_box_infinite.Enable(False)

                # update the top panel
                if self.top_panel != None:
                    self.top_panel.SetCurrentModeIcon('record')
                
            else:
                #invalid state, stop and start again
                self.matrox_frame_grabber.StopCapture()
                self.matrox_frame_grabber.StartCapture()

        if event != None:
            event.Skip()
    def OnStopButton(self, event):

        """Stopping the live or record modes if needed
        """
        if self.matrox_frame_grabber != None:
            self.matrox_frame_grabber.StopCapture()

        if event != None:
            event.Skip()

    #######################################################################
    #                       live mode functions                           #
    #######################################################################
    
    def OnLiveButton(self, event):

        """Starting/stopping the live mode.
        """
        if self.matrox_frame_grabber != None:
            current_state = self.matrox_frame_grabber.GetCurrentState()
            # Perform some control depending on what state we were in
            if current_state == MatroxFramegrabber.STOPPED:
                self.matrox_frame_grabber.StartCapture()
            elif current_state == MatroxFramegrabber.LIVE:
                self.matrox_frame_grabber.StopCapture()
            elif current_state == MatroxFramegrabber.RECORDING:
                self.matrox_frame_grabber.StopRecording()
            elif current_state == MatroxFramegrabber.PAUSED:
                self.matrox_frame_grabber.ResumeCapture()
            elif current_state == MatroxFramegrabber.PAUSED_RECORDING:
                self.matrox_frame_grabber.ResumeCapture()
            else:
                #invalid state, stop and start again
                self.matrox_frame_grabber.StopCapture()
                self.matrox_frame_grabber.StartCapture()


        if event != None:
            event.Skip()


    #######################################################################
    #                       record mode functions                         #
    #######################################################################      
    
    def OnRecordButton(self, event):

        """Starting/stopping the record mode.
        """
        if self.matrox_frame_grabber != None:
            current_state = self.matrox_frame_grabber.GetCurrentState()


            ## 2015/12/08 - RFC addition:
            ## Added code to optionally trigger the onelight when a record button is pressed.
##            sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
##
##            MAC_IP   = "170.166.249.171"
##            MAC_PORT = 2007
##
##            sock.sendto("Testing one two three", (MAC_IP,MAC_PORT)) 

            # Get the avi files that we want to write to
            acq_settings = self.GetParent().GetCurrentSettings()['image_acquisition_settings']

            # get the number of frames we wisth to write
            if acq_settings['record_fixed_number_of_frames_boolean']:
                n_frames = acq_settings['n_frames_to_record']
            else:
                n_frames = -1
                
            # Perform some control depending on what state we were in
            if current_state == MatroxFramegrabber.RECORDING:
                self.record_button.SetValue(True)
            elif current_state == MatroxFramegrabber.PAUSED_RECORDING:
                self.matrox_frame_grabber.ResumeCapture()
            else:
                # Start the recording
                # check the paths of the videos
                paths_valid, message = self.CheckThatPathsExist()
                if paths_valid:

                    # format the avi files for the matrox framegrabber
                    self._formatted_files_dictionary = self.GetFormattedAVIFileNames(acq_settings)
                    self.matrox_frame_grabber.StartRecording(MatroxFramegrabber.IntStringMap(self._formatted_files_dictionary), n_frames)
                    # After starting recording, mark the location on the fixation GUI by sending a 1 to the capture Queue.
                    if self.fixQ is not None:
                        try:
                            # 0 is for acquisition changes
                            bottom_pannel_settings = self.GetCurrentSettings()
                            self.fixQ.put((0,bottom_pannel_settings['current_movie_number']),block=False,timeout=0)
                        except:
                            pass
                else:
                    # starting the recording failed so reset the button
                    self.record_button.SetValue(False)
                    wx.MessageBox(message)
                
        if event != None:
            event.Skip()

    def GetLastFileNamesRecorded(self):

        return copy.deepcopy(self._formatted_files_dictionary)

    def CheckThatPathsExist(self):
        
        # Get the avi files that we want to write to
        acq_settings = self.GetParent().GetCurrentSettings()['image_acquisition_settings']
        
        # extract settings
        directories_all  = acq_settings['destination_folders']
        file_names_all   = acq_settings['current_file_names']
        enabled_channels = acq_settings['enabled_channels']

        message = ""
        
        # Stage the enabled channels in the dictionary
        for current_channel_index in range(len(enabled_channels)):
            if enabled_channels[current_channel_index]:
            
                 # check the channel
                if not os.path.exists(directories_all[current_channel_index]):
                    message = "The path " + directories_all[current_channel_index] + " does not exist.\n" + \
                                  "Please choose a different location and try again"
                    return (False, message)
                else:
                    # check permissions
                    try:
                        current_file = directories_all[current_channel_index] + "\\testing_access.txt"
                        f = open(current_file, 'w')
                        f.close()

                        os.remove(current_file)
                    except IOError as e:
                        message = "You do not have write access to " + directories_all[current_channel_index] + "\n" + \
                                      "Please choose a different location and try again"
                        return (False, message)

        return (True, message)
            
    def GetFormattedAVIFileNames(self, acq_settings):

        """
        """

        # the formatted dictionary to return
        return_dictionary = {}

        # we also want to keep a dictionary of the meta data files
        self.metadata_file_names = {}

        # extract settings
        directories_all  = acq_settings['destination_folders']
        file_names_all   = acq_settings['current_file_names']
        enabled_channels = acq_settings['enabled_channels']

        # ensure the sizes are the same
        if (len(enabled_channels) != len(file_names_all)) or \
            (len(enabled_channels) != len(directories_all)):
            return return_dictionary

        # Stage the enabled channels in the dictionary
        for current_channel_index in range(len(enabled_channels)):
            if enabled_channels[current_channel_index]:
            
                # combine the file names and directories
                current_file = directories_all[current_channel_index] + "\\" + file_names_all[current_channel_index]
            
                # remove .avi file extensions
                if current_file[(len(current_file)-4):len(current_file)].lower() == '.avi':
                    current_file = current_file[0:(len(current_file) - 4)]
                
                return_dictionary[current_channel_index] = current_file

        # Now we must check to see if any of the files exist and if they do we must
        # increment the number extension
        bottom_pannel_settings = self.GetCurrentSettings()
        movie_number = bottom_pannel_settings['current_movie_number']

        file_exists = True

        while file_exists:
            
            file_exists = False
            
            # the the files of every enabled channel
            for current_key in return_dictionary.keys():

                base_file_name = return_dictionary[current_key]
                
                # construct the full file nmae
                current_file_name  = str(base_file_name + "_%04d" % movie_number + '.avi')
                metadata_file_name = str(base_file_name + "_%04d" % movie_number + '.mat')
                
                if os.path.exists(current_file_name) or os.path.exists(metadata_file_name):
                    file_exists = True

            # if any of the files exist with this movie number, incremenet it
            if file_exists:
                movie_number += 1

        # update the dictionary with the full path
        for current_key in return_dictionary.keys():

            base_file_name = return_dictionary[current_key]
            # construct the full file nmae
            return_dictionary[current_key]        = str(base_file_name + "_%04d" % movie_number + '.avi')
            self.metadata_file_names[current_key] = str(base_file_name + "_%04d" % movie_number + '.mat')


        # update the control with the movie number that will not conflict with other
        # files in any of the directories chosen
        self.movie_number_ctrl.SetValue(movie_number+1)

        self.current_movie_number = movie_number

        return return_dictionary

    def OnGrabFinished(self, event):

        # all we want to do here is write the metadata to file

        settings_dictionary = self.GetParent().GetCurrentSettings()
        
        settings_dictionary['frame_time_stamps'] = self.matrox_frame_grabber.GetLastAcquisitionTimeStampsFromPython()
        settings_dictionary['frame_numbers']     = self.matrox_frame_grabber.GetAVIFrameNumbersFromPython()
        
        for current_channel in self.metadata_file_names:
            sio.savemat(self.metadata_file_names[current_channel], settings_dictionary, format = '5', long_field_names = True, oned_as = 'column')

        if event != None:
            event.Skip()

###################################################################
#                           Test code                             #
###################################################################

if __name__ == '__main__':

    initial_settings = {'record_fixed_number_of_frames_boolean': True,
                        'n_frames_to_record':                    200}

    # initializing the application
    app              = wx.App()
  
    # initializing the window
    test_frame       = wx.Frame(None,
                                size  = (700, 140),
                                title = 'wxSaviorImageAcquisitionPanel test')

    test_frame.SetBackgroundColour('black')
    test_frame.SetForegroundColour('white')

    # creating panel
    test_panel      = wxSaviorBottomPanel(test_frame, initial_settings)

    test_frame.Bind(wx.EVT_CLOSE, test_panel.OnClose)
    
    test_frame.Show()

    # starting the main event loop
    app.MainLoop()
     
