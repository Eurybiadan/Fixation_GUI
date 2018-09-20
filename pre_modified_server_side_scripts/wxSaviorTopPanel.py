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
import wx
import wx.lib.throbber as  throb
import MatroxFramegrabber
import numpy as np

class wxSaviorTopPanel(wx.Panel):

    """Image acquisition control panel
    """
    
    def __init__(self,
                 parent,
                 matrox_frame_grabber_wx_event_generator,
                 local_savior_path = '.'):

        """
        """        

        # default constructor using the parent window        
        wx.Panel.__init__(self, parent, -1)

        self._matrox_frame_grabber_wx_event_generator = matrox_frame_grabber_wx_event_generator
        self._matrox_frame_grabber                    = matrox_frame_grabber_wx_event_generator.GetEventGenerator()
        self._matrox_frame_grabber_wx_event_generator.BindWXEvent("stats_ready", self._OnStatsUpdate)

        self.movie_number = 0

        # If we have a fixation GUI open, grab its reference
        if parent.fixQ is not None:
            self.fixQ = parent.fixQ


        # getting background and foreground colours from the parent panel
        self.SetBackgroundColour(parent.GetBackgroundColour())
        self.SetForegroundColour(parent.GetForegroundColour())           

        # creating the sizer and defining control dimensions
        main_sizer             = wx.GridBagSizer(vgap = 10, hgap = 10)
        border                 = 0
        text_ctrl_width        = 40
        text_ctrl_height       = 15
        text_ctrl_size         = (text_ctrl_width, text_ctrl_height)
        
        # Defining the title font
        bold_font = self.GetFont()
        bold_font.SetWeight(wx.BOLD)
        bold_font.SetPointSize(bold_font.GetPointSize() + 2)
        self.SetFont(bold_font)

        
        ###################################################################
        #                      creating controls                          #
        ###################################################################


        # discard and image recording section #######################
        blank_icon                  = wx.Bitmap(local_savior_path + '/icons/blank icon.png',                 wx.BITMAP_TYPE_PNG)
        stop_icon                   = wx.Bitmap(local_savior_path + '/icons/Pause-Hot-icon 42.png',          wx.BITMAP_TYPE_PNG)
        live_icon                   = wx.Bitmap(local_savior_path + '/icons/play-normal-blue-bright 42.png', wx.BITMAP_TYPE_PNG)
        record_icon                 = wx.Bitmap(local_savior_path + '/icons/Record-Pressed-icon 42.png',     wx.BITMAP_TYPE_PNG)

        # creating the throbbers (initially in resting mode)
        self.mode_icons             = [stop_icon, live_icon, record_icon, blank_icon]        
        throbber_delay              = 0.35
        self.current_mode_throbber = throb.Throbber(self, -1, self.mode_icons, frameDelay = throbber_delay)

        self.SetCurrentModeIcon('stop')
        
        # adding controls to the sizer
        main_sizer.Add(self.current_mode_throbber,
                       pos  = (0, 1),                               span   = (5, 1),
                       flag = wx.ALIGN_CENTER_VERTICAL|wx.ALL,      border = 0)

        label_acquisition_frame_rate_title = wx.StaticText(self, label = "Acquisition frame rate (FPS): ", style = wx.ALIGN_LEFT)
        self._acquisition_frame_rate_label = wx.StaticText(self, label = '0.0', style = wx.ALIGN_LEFT)


        self._video_writing_frame_rate_title   = wx.StaticText(self, label = "Writing frame rate (FPS): ")
        self._video_writing_rate_label   = wx.StaticText(self, label = '0.0')

        self._video_writing_frame_rate_title.Show(False)
        self._video_writing_rate_label.Show(False)
        self._video_number_label         = wx.StaticText(self, label = 'Not recording')
        self._video_frames_written_label = wx.StaticText(self, label = '0/0')

        self._video_frames_written_label.Show(False)

        main_sizer.Add(label_acquisition_frame_rate_title,
                       pos  = (1,  2),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALL | wx.ALIGN_LEFT,                   border = border)
        main_sizer.Add(self._acquisition_frame_rate_label,
                       pos  = (1,  3),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, border = border)

        # size headers ####################################################
        self.temp_header_H               = wx.StaticText(self, label = "  H  ")
        self.temp_header_V               = wx.StaticText(self, label = "  V  ")

        # adding controls to the sizer
        main_sizer.Add(self.temp_header_H,
                       pos  = (1,  5),                              span   = (1, 1),
                       flag = wx.ALIGN_CENTER | wx.ALL, border = border)
        main_sizer.Add(self.temp_header_V,
                       pos  = (1,  6),                              span   = (1, 1),
                       flag = wx.ALIGN_CENTER | wx.ALL, border = border)

        # Image size in degrees  ##########################################
        label_text_imaging_fov_in_deg    = wx.StaticText(self, label = "Field of view (deg):")
        self.text_imaging_width_in_deg   = wx.StaticText(self, label = "2.0")
        self.text_imaging_width_in_deg.SetMinSize((text_ctrl_width, -1))       
        label_imaging_x_in_deg           = wx.StaticText(self, label = "x")
        self.text_imaging_height_in_deg  = wx.StaticText(self, label = "2.0")

        # Frame size in pixels ############################################
        label_frame_size_in_pix          = wx.StaticText(self, label = "Image size (pix):")
        label_frame_size_in_pix.SetMinSize((2*text_ctrl_width, -1))     
        self.text_frame_width_in_pix     = wx.StaticText(self, label = "     ")
        self.text_frame_width_in_pix.SetMinSize((text_ctrl_width, -1))       
        label_frame_size_x               = wx.StaticText(self, label =  "x")
        self.text_frame_height_in_pix    = wx.StaticText(self, label = "     ")

        # adding controls to the sizer
        current_row = 2

        main_sizer.Add(self._video_writing_frame_rate_title,
                       pos  = (current_row,  2),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALL| wx.ALIGN_LEFT,                   border = border)
        main_sizer.Add(self._video_writing_rate_label,
                       pos  = (current_row,  3),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALIGN_LEFT| wx.ALL, border = border)

        main_sizer.Add(label_text_imaging_fov_in_deg,
                       pos  = (current_row,  4),                    span   = (1, 1),
                                          border = border)
        main_sizer.Add(self.text_imaging_width_in_deg,
                       pos  = (current_row,  5),                    span   = (1, 1),
                       border = border)
        main_sizer.Add(label_imaging_x_in_deg,
                       pos  = (current_row,  6),                    span   = (1, 1),
                       border = border)
        main_sizer.Add(self.text_imaging_height_in_deg,
                       pos  = (current_row, 7),                    span   = (1, 1),
                       border = border)

        current_row += 1
        main_sizer.Add(self._video_number_label,
                       pos  = (current_row,  2),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, border = border)

        main_sizer.Add(self._video_frames_written_label,
                       pos  = (current_row,  3),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALIGN_LEFT | wx.ALL, border = border)

        main_sizer.Add(label_frame_size_in_pix,
                       pos  = (current_row,  4),                    span   = (1, 1),
                       border = border)
        main_sizer.Add(self.text_frame_width_in_pix,
                       pos  = (current_row,  5),                    span   = (1, 1),
                       border = border)
        main_sizer.Add(label_frame_size_x,
                       pos  = (current_row,  6),                    span   = (1, 1),
                       border = border)
        main_sizer.Add(self.text_frame_height_in_pix,
                       pos  = (current_row, 7),                    span   = (1, 1),
                       border = border)

        current_row += 1
        main_sizer.AddSizer((0,0),
                       pos  = (current_row, 10),                    span   = (1, 1),
                       flag = wx.EXPAND | wx.ALIGN_CENTER | wx.ALL, border = border)

        # making some columns and row growables
        #main_sizer.AddGrowableCol( 0, proportion = 1)
        main_sizer.AddGrowableCol( 2, proportion = .6)
        main_sizer.AddGrowableCol( 3, proportion = .4)
        # main_sizer.AddGrowableCol( 6, proportion = 2)
        # main_sizer.AddGrowableCol(12, proportion = 2)

        # Fitting the current panel to the needs of the sizer.
        self.SetSizerAndFit(main_sizer)

        # bind the onclose method
        wx.GetApp().GetTopWindow().Bind(wx.EVT_CLOSE, self.OnClose, wx.GetApp().GetTopWindow())
        self._main_sizer = main_sizer

        # end of constructor ##############################################

    def _OnStatsUpdate(self, event):

        matrox_frame_grabber =  self._matrox_frame_grabber_wx_event_generator.GetEventGenerator()

        if matrox_frame_grabber.GetCurrentState() == MatroxFramegrabber.RECORDING or\
            matrox_frame_grabber.GetCurrentState() == MatroxFramegrabber.PAUSED_RECORDING:

            self._video_writing_frame_rate_title.Show(True)
            self._video_writing_rate_label.Show(True)
            self._video_number_label.Show(True)
            self._video_frames_written_label.Show(True)
            self._main_sizer.Layout()
            avi_writing_frame_rate = matrox_frame_grabber.GetAVIWritingFrameRate()
            avi_writing_frame_rate = np.around(avi_writing_frame_rate, 2)

            avi_frames_written     = matrox_frame_grabber.GetCurrentAVIFrameNumber()
            avi_frames_to_write    = matrox_frame_grabber.GetNumberOfAVIFramesToWrite()


            self._video_writing_rate_label.SetLabel(str(avi_writing_frame_rate))

            saving_video_label   = "Saving movie # " + str(self.movie_number)
            frames_written_label = str(avi_frames_written) + '/' + str(avi_frames_to_write)

            self._video_number_label.SetLabel(saving_video_label)
            self._video_frames_written_label.SetLabel(frames_written_label)
        else:
            self._video_writing_frame_rate_title.Show(False)
            self._video_writing_rate_label.Show(False)
            self._video_number_label.Show(False)
            self._video_frames_written_label.Show(False)

        acquisition_rate = matrox_frame_grabber.GetAcquisitionFrameRate()
        display_rate     = matrox_frame_grabber.GetDisplayFrameRate()
        display_rate     = np.around(display_rate, 2)
        acquisition_rate     = np.around(acquisition_rate, 2)
        self._acquisition_frame_rate_label.SetLabel(str(acquisition_rate))

        self.Update()

        event.Skip()

    def OnClose(self, event):

        self.current_mode_throbber.Rest()
        event.Skip()

    def SetCurrentModeIcon(self, current_mode):

        """
        """

        if current_mode == 'live':
            # hiding the pause throbber
            self.current_mode_throbber.Stop()
            self.current_mode_throbber.SetSequence([1, 3])
            #self.current_mode_throbber.Start()

        elif current_mode == 'record':

            self.current_mode_throbber.Stop()
            self.current_mode_throbber.SetSequence([2, 3])
            #self.current_mode_throbber.Start()
            
        else:
            
            self.current_mode_throbber.Stop()
            self.current_mode_throbber.SetSequence([0, 0])

        # Force a repaint event
        self.Refresh()

    def ShowEyeTrackingIcon(self, boolean):
        ""
        ""
        pass
        #self.eye_tracking_icon.Show(boolean)
        
    def UpdateOpticalScannersAndImageSamplingDisplay(self,frame_width_in_deg,
                                                           frame_height_in_deg):

        """
        """

        frame_width_in_pix = self._matrox_frame_grabber.GetVideoWidth()
        frame_height_in_pix =  self._matrox_frame_grabber.GetVideoHeight()

        # getting sizes to guarantee alignment
        temp_size_left  = self.text_frame_width_in_pix.GetSize()
        temp_size_right = self.text_frame_height_in_pix.GetSize()

        # Frame size in pixels
        self.text_frame_width_in_pix.SetLabel(    str(frame_width_in_pix))
        self.text_frame_height_in_pix.SetLabel(   str(frame_height_in_pix))

        self.text_imaging_width_in_deg.SetLabel(  str(round(frame_width_in_deg,  2)))
        self.text_imaging_height_in_deg.SetLabel( str(round(frame_height_in_deg, 2)))

        # Update the fixation GUI as well
        if self.fixQ is not None:
            try:
                # 1 is for FOV changes
                self.fixQ.put( (1, round(frame_width_in_deg,  2),round(frame_height_in_deg,  2)),block=False, timeout=0 )
            except:
                pass

        # adjusting sizes 
        self.text_frame_width_in_pix.SetSize(     temp_size_left)
        self.text_frame_height_in_pix.SetSize(    temp_size_right)
        self.text_imaging_width_in_deg.SetSize(   temp_size_left)
        self.text_imaging_height_in_deg.SetSize(  temp_size_right)

    def SetCurrentMovieNumber(self, movie_number):
        self.movie_number = movie_number

###################################################################
#                           Test code                             #
###################################################################

class TestApp(wx.App):

    def __init__ (self):

        wx.App.__init__(self)

        # initializing the window
        test_frame       = wx.Frame(None,
                                    size  = (700, 250),
                                    title = 'wxSaviorImageAcquisitionPanel test')


        self.SetTopWindow(test_frame)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # creating panel
        self.test_panel      = wxSaviorTopPanel(test_frame)

        self.test_panel.UpdateOpticalScannersAndImageSamplingDisplay(
                             frame_width_in_pix            = 800,
                             frame_height_in_pix           = 750,
                             frame_width_in_deg            = 1.8,
                             frame_height_in_deg           = 1.7)

        sizer.Add(self.test_panel, wx.GROW)

        live_button = wx.Button(test_frame, label = "Start Live")
        sizer.Add(live_button)
        live_button.Bind(wx.EVT_BUTTON, self.OnLive)

        record_button = wx.Button(test_frame, label = "Start Record")
        sizer.Add(record_button)
        record_button.Bind(wx.EVT_BUTTON, self.OnRecord)
        
        stop_button = wx.Button(test_frame, label = "Stop")
        sizer.Add(stop_button)
        stop_button.Bind(wx.EVT_BUTTON, self.OnStop)
        
        test_frame.SetSizer(sizer)
        test_frame.Show()

        # starting the main event loop
        self.MainLoop()

    def OnLive(self, event):
        self.test_panel.SetCurrentModeIcon('live')
        event.Skip()

    def OnRecord(self, event):
        self.test_panel.SetCurrentModeIcon('record')
        event.Skip()

    def OnStop(self, event):
        self.test_panel.SetCurrentModeIcon('stop')
        event.Skip()

if __name__ == '__main__':


    # initializing the application
    app              = TestApp()
  
     
