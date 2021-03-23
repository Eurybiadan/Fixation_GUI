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
#  Medical College of Wisconsin                 *
#  All Rights Reserved                          *
#                                               *
#  Zachary Harvey (zgh7255@gmail.com)           *
#  Alfredo Dubra  (adubra@mcw.edu)              *
#                                               *
#  Eye Institute                                *
#  Medical College of Wisconsin                 *
#  Milwaukee WI 53226                           *
#************************************************


# TODO: the top panel does not update to reflect the FOV or the image size.
#       It should update whenever a new settings file is loaded or when the
#       floatspin controls in the optical scanners panel are updated.

# TODO: I think that the video panel is hiding the first line of the live
#       image. If so, could it be possible that we are not
#       showing the first column too? I came across having to add a +1 in
#       TsunamiWave Clinical recently and that makes me thing that this is
#       necessary in this case too.

# TODO: When selecting the settings file that say "full_scan" that also include
#       the backscan portion of the scanner, we get an error. I know that you
#       didn't have time to fix the video tiling, but it would be good if we could
#       see the video even if we have to drag the window around.

# TODO: In the exposure settings panel, when the modulation only happens in
#       the vertical direction, checking the box to enable/disable the
#       modulation does not turn the laser on/off as expected. When the vertical
#       only checkbox in unchecked, everything works well.

# TODO: not urgent. Add text "Saving movie # ..." in the bottom panel and
#       changed to "Last saved movie(s) #...". This whouls be in large
#       font below the play/pause/record buttons.

# TODO: when we bring the eye-tracking back to life, we should be
#       able to load a previous image as a reference frame. This
#       will be key for follow up studies (most of what we want
#       to do.

# TODO: remind me to talk about an conference in Virginia in June.

# importing Python libraries
import os, wx, time, threading, pickle, winsound, string, copy
import wx.lib.agw.flatnotebook as fnb
import wx.lib.newevent
import numpy as np     
import wx.lib.agw.advancedsplash as AS
import scipy.io as sio
import zmq
import yaml
import LiveStreamMathDisplay
import NystagmusCorrectionWindow

# contains the local path for the savior fvile structure
import SaviorHardwareConfiguration

# Import the fixation GUI.
from wxFixProc import FixGUIServer
from multiprocessing import Queue
from threading import Thread

import SaviorResearchPanel
import SaviorClinicalPanel

import sys

# changing cwd so that we know where all of the files are.
os.chdir(SaviorHardwareConfiguration.local_path)

# TODO: implement shutter safety.

# importing home-made user interface modules
import wxSaviorTopPanel, wxSaviorImageAcquisitionPanel, VideoDisplay, \
       wxSaviorOpticalScannersPanel, wxSaviorEyeTrackingPanel, \
       wxSaviorBottomPanel, wxTrackingFrameDisplay, wxSaviorSettingsFileGrid, \
       wxEventGenerator, SaviorCommandInterface,   \
       ParseDCFFile, wxSaviorExposureSignalsDialog, IlluminationControlFrame
       
# importing hardware control modules
import MatroxFramegrabber, SignalGenerator

version = 2.0

# Auxiliary function
def __MultipleBeeps__(n_beeps              = 1,   t_between_beeps_in_s = 0.3,
                      beep_frequency_in_Hz = 325, beep_duration_in_ms  = 30):

    """Auxiliary function that beeps n_beeps times separated by
       t_between_beeps_in_s. The thread waits between beeps by calling
       the funcion sleep from the module time.
    """
    for index in range(n_beeps - 1):
        winsound.Beep(beep_frequency_in_Hz, beep_duration_in_ms)
        time.sleep(t_between_beeps_in_s)
        
    winsound.Beep(beep_frequency_in_Hz, beep_duration_in_ms)



import collections

def RecursiveDictionaryUpdate(d, u):
    for k, v in u.iteritems():
        if isinstance(v, collections.Mapping):
            r = RecursiveDictionaryUpdate(d.get(k, {}), v)
            d[k] = r
        else:
            d[k] = u[k]
    return d


###########################################################################    
#                         Main application class                          #
###########################################################################    

software_configuration_dictionary = {'button_color' : (50, 50, 50),
                                     'button_height' : 25}

class SaviorApp(wx.App):
    
    """This class implements the image acquisition part of a scanning laser
       ophthalmoscope (SLO). The application handles communication from our 
       Matrox Imaging Library (MIL) control module that controls a Helios
       framegrabber, an eye tracking module that uses a CUDA-enabled Nvidia
       graphics card, and a National Instruments box that acts as a signal
       generator that controls the optical scanners. 
    """

    # TODO: we should make sure in a couple of weeks that the clinical boolean works.
    def __init__(self, clinical_version, initial_settings):
        
        """Application constructor that requires a dictionary containing
           the SLO hardware and GUI settings. See the file
           SaviorSettings.pyw for an up to date example of the dictionary
           that is required here.
        """      
       
        # creating the application
        wx.App.__init__(self, redirect = False)



        # initialize this to none
        self.sync_loss_thread = None
                                  
        # creating internal flag
        self.initialized      = False
       
        # Formatting the settings
        settings              = {'clinical_version'                      : clinical_version,
                                 'optical_scanners_settings'             : initial_settings.optical_scanners_settings,    
                                 'image_resolution_calculation_settings' : initial_settings.image_resolution_calculation_settings,
                                 'image_acquisition_settings'            : initial_settings.image_acquisition_settings,
                                 'eye_tracking_settings'                 : initial_settings.eye_tracking_settings,
                                 'secondary_display_settings'            : initial_settings.secondary_display_settings}

        # initializing the hardware and GUI
        self.LoadConfiguration(settings)

        # starting the main event loop
        self.MainLoop()      

    def LoadConfiguration(self, new_settings):
    
        """Updating the SLO and imaging acquisition settings. See the file
           SaviorSettings.pyw for an up to date example of the dictionary
           that is required here. 
        """
        
        # keeping an internal copy of the new settings
        if self.initialized:

            self.settings['optical_scanners_settings'].update(new_settings['optical_scanners_settings'])
            self.settings['image_acquisition_settings'].update(new_settings['image_acquisition_settings'])
            self.settings['image_resolution_calculation_settings'].update(new_settings['image_resolution_calculation_settings'])
            self.settings['secondary_display_settings'].update(new_settings['secondary_display_settings'])

            if 'eye_tracking_settings' in self.settings.keys() and\
                    'eye_tracking_settings' in new_settings.keys():
                self.settings['eye_tracking_settings'].update(new_settings['eye_tracking_settings'])

        else:
            self.settings                       = new_settings

        # The settings passed here will never contain the hardware information
        # Grabbing the stuff from the hardware configuration file
        self.settings['optical_scanners_settings'].update(  SaviorHardwareConfiguration.optical_scanners_settings  )
        self.settings['image_acquisition_settings'].update( SaviorHardwareConfiguration.image_acquisition_settings )

        # make sure we are in the right directory
        os.chdir(SaviorHardwareConfiguration.local_path)

        #############################
        # Setting up Matrox Framegrabber
        #############################
            
        # Create the matrox frame grabber
        self.DCF_file_name                            = self.settings['image_acquisition_settings']['DCF_file']
        self.n_lines_per_strip                        = self.settings['image_acquisition_settings']['n_lines_per_strip']
        self.n_lines_between_strip_starts             = self.settings['image_acquisition_settings']['n_lines_between_strip_starts']

        if self.initialized:

            # Tell MIL to not acquire any more frames
            self.matrox_frame_grabber.StopCapture()

            for index in range(len(self._display_windows)):
                # unbind this first so the callback is not called while we destroy them
                self._display_windows[index].Unbind(wx.EVT_CLOSE)
                self._display_windows[index].Close()
                self._display_windows[index].Destroy()

            self._display_windows = []


            # # wait for any previous frames to be processed
            # self.matrox_frame_grabber.StopEventDispatchPython()
            # set the new DCF file
            self.matrox_frame_grabber.SetDCF(self.DCF_file_name)


        else:
            self.matrox_frame_grabber                 = MatroxFramegrabber.MatroxFramegrabber(self.DCF_file_name)

            events_to_not_wrap_wx_events_around       = ['frame_arrived', 'frame_processed', 'strip_arrived'] # these will happen too often
            self.matrox_frame_grabber_event_generator = wxEventGenerator.wxEventGenerator(self.matrox_frame_grabber,
                                                                                          self,
                                                                                          events_to_not_wrap_wx_events_around)

            # bind relavent events to give feedback to the user
            self.matrox_frame_grabber_event_generator.BindWXEvent("state_changed", self.OnMatroxStateChange)
            self.matrox_frame_grabber_event_generator.BindWXEvent("grab_finished", self.OnGrabFinished)
            self.matrox_frame_grabber_event_generator.BindWXEvent("grab_error", self.OnMatroxGrabError)


        # get a list of channels that are not availabe for imaging based on
        # the DCF file and disable them from the acquisition panel
        self.dig_num                                  = self.matrox_frame_grabber.GetDigitizerNumber()
        self.n_channels                               = self.matrox_frame_grabber.GetNumberOfChannels()

        # Tell the mil_control to flip if the settings ask for it
        for cur_channel_index in range(self.n_channels):
            self.matrox_frame_grabber.FlipVertical(  self.settings['image_acquisition_settings']['flip_displays_up_down'],    cur_channel_index)
            self.matrox_frame_grabber.FlipHorizontal(self.settings['image_acquisition_settings']['flip_displays_left_right'], cur_channel_index)

        # determining how fast we should update statistics on the display panel
        self.stats_update_rate_in_updates_per_second   = self.settings['image_acquisition_settings']['stats_update_rate_in_Hz']
        update_every_n_frames                          = np.ceil(np.float(self.matrox_frame_grabber.GetFrameRate()) /\
                                                                 np.float(self.stats_update_rate_in_updates_per_second))
        self.matrox_frame_grabber.SetStatisticsUpdateRate(long(self.stats_update_rate_in_updates_per_second))

        # Set the timeout period for syncronization loss as a multiple of the frame period
        time_out                                      = 20
        self.matrox_frame_grabber.SetSyncronizationTimeoutPeriod(time_out) # timeout = time_out*frame_period

        # Pass some information about the image acquisition to the optical scanners panel
        DCF_data = ParseDCFFile.ParseDCFFile(self.settings['image_acquisition_settings']['DCF_file'])

        # set the black and white reference values if they exist
        if 'black_reference' in self.settings['image_acquisition_settings']:

            for cur_channel_index in range(self.n_channels):
                self.matrox_frame_grabber.SetBlackReference(self.settings['image_acquisition_settings']['black_reference'][cur_channel_index], cur_channel_index)
                
        if 'white_reference' in self.settings['image_acquisition_settings']:

            for cur_channel_index in range(self.n_channels):
                self.matrox_frame_grabber.SetWhiteReference(self.settings['image_acquisition_settings']['white_reference'][cur_channel_index], cur_channel_index)

        #############################
        # Setting up NI signal generator
        #############################

        # initialize these to zero
        # when the GUI is updated, it will send the correct voltages
        self.settings ['optical_scanners_settings']['raster_scanner_amplitude_in_volts']   = 0
        self.settings ['optical_scanners_settings']['resonant_scanner_amplitude_in_volts'] = 0

        # specify a default exposure timing as the active area of the image
        # vertical exposure signal (in units of lines based on data from the DCF file)
        start_line = DCF_data['VDT_VBPORCH'] + DCF_data['VDT_VSYNC']
        stop_line  = start_line              + DCF_data['VDT_VACTIVE']

        # determine the timing values for the active area based on DCF data
        T0         = DCF_data['VDT_HBPORCH'] + DCF_data['VDT_HSYNC']
        T1         = DCF_data['VDT_HACTIVE']
        
        self.settings['optical_scanners_settings']['default_exposure_timing'] = [start_line, stop_line, T0, T1]
        
        # Create the NI signal generator
        if self.initialized:
            # self.signal_generator.SetVoltages(self.settings ['optical_scanners_settings'])
            self.signal_generator.SetDefaultExposureTiming([start_line, stop_line, T0, T1])
        else:
            self.signal_generator                     = SignalGenerator.SignalGenerator(
                                                            self.settings ['optical_scanners_settings'])

        # update the pll info for the signal generator
        self.signal_generator.SetMatroxPLLScaling(float(DCF_data['VDT_HTOTAL']))

        # set the exposure settings
        exposure_settings = self.settings ['optical_scanners_settings']['exposure_settings']
        self.signal_generator.SetExposureSettings(exposure_settings)        

        ############# set the illumination modes
        illumination_settings = self.settings['optical_scanners_settings']['illumination_settings']
        self.signal_generator.SetEveryNFramesIllumination(illumination_settings['every_N'])

        for current_channel in range(self.n_channels):
            
            illumination_mode = 0
            if illumination_settings['modes'][current_channel] == 'standard':
                illumination_mode = 0
            elif illumination_settings['modes'][current_channel] == 'monoshot':
                illumination_mode = 1
            elif illumination_settings['modes'][current_channel] == 'every_N':
                illumination_mode = 2
                
            self.signal_generator.SetIlluminationMode(current_channel, illumination_mode)

        #############################
        # Setting up user interface
        #############################

        # information retrieved by the DCF file that needs to be sent to the GUI panels
        self.settings['image_acquisition_settings']['digitizer_number']                        = self.dig_num
        self.settings['image_acquisition_settings']['n_channels']                              = self.n_channels

         # Getting the video information for the optical scanners page
        self.settings['optical_scanners_settings']['visible_lines_in_frame']                   = self.matrox_frame_grabber.GetVideoHeight()
        self.settings['optical_scanners_settings']['total_lines_in_frame']                     = DCF_data['VDT_VTOTAL']
        self.settings['optical_scanners_settings']['n_pixels_per_line']                        = self.matrox_frame_grabber.GetVideoWidth() 
        self.settings['optical_scanners_settings']['pixel_clock_in_MHz']                       = self.matrox_frame_grabber.GetPixelClockFrequencyHz()/1000000

        # This value will be determined later when the video signal module is created
        # and this can be measured. The panel will raise a key error if this item is not in the dictionary
        self.settings['optical_scanners_settings']['resonant_scanner_frequency_in_KHz']      = self.signal_generator.GetResonantScannerFrequencyInkHz()

        # Always display stats at the top
        self.display_video_stats_horizontal = True

        channel_numbers = range(self.n_channels)

        video_display_settings = {}
        video_display_settings['channel_labels']             = self.settings['image_acquisition_settings']['channel_labels'][0:self.n_channels]
        video_display_settings['stats_font_size']            = 14
        video_display_settings['horizontal_stats']           = self.display_video_stats_horizontal
        video_display_settings['video_tiling_configuration'] = self.settings['image_acquisition_settings']['video_tiling_configuration']

        if self.initialized:

            # if the synchronization was lost, stop the beebing thread
            if self.sync_loss_thread != None:
                self.warning_user_of_sync_loss = False
                self.sync_loss_thread.join()
                self.sync_loss_thread          = None
                self.savior_panel.top_panel.SetBackgroundColour('default')

            # update the savior GUI
            self.savior_panel.SetCurrentSettings(self.settings)

            # start the matrox frame grabber
            self.matrox_frame_grabber.StartCapture()

        else:
            # If synchronization is lost then we launch a thread to beep
            # to inform the user
            self.sync_loss_thread              = None
            
            # create defaults
            self.display_window_pos            = (0, 0)
        
            # Load the icon
            self.savior_icon   = wx.Icon('icons/Record-Pressed-icon 16.ico', wx.BITMAP_TYPE_ICO)
            
            # Create the two queues we'll post to in order to pass and recv messages from
            # the fixation GUI
            self.fixQ = Queue(1)
            self.recvQ = Queue(1)
            
            # creating application main frame
            if self.settings['clinical_version']:
                self.savior_panel  = SaviorClinicalPanel.SaviorMainPanel(self.settings,
                                                                    self.LoadConfiguration,
                                                                    self.savior_icon,
                                                                    self.matrox_frame_grabber_event_generator,
                                                                    self.signal_generator,
                                                                    self.fixQ,
                                                                    software_configuration_dictionary)

            else:
                self.savior_panel  = SaviorResearchPanel.SaviorMainPanel(self.settings,
                                                                    self.LoadConfiguration,
                                                                    self.savior_icon,
                                                                    self.matrox_frame_grabber_event_generator,
                                                                    self.signal_generator,
                                                                    self.fixQ,
                                                                    self.fixQ,
                                                                    software_configuration_dictionary)

            # update the savior GUI
            self.savior_panel.SetCurrentSettings(self.settings)


            # bringing the application window to the front
            self.SetTopWindow(self.savior_panel)

            # We want the scanner signals to go to zero at shutdown so we will bind an on close event
            self.savior_panel.Bind(wx.EVT_CLOSE, self.OnClose)

            # bind key press events so we can disable the anoying warnings
            self.Bind(wx.EVT_KEY_DOWN, self.OnKeyDown)

            # start the matrox frame grabber
            self.matrox_frame_grabber.StartCapture()

            #########################################################
            ## wxFixation GUI addition by Robert Cooper 09-19-2018 ##
            #########################################################
            self.wxFixFrameProc = FixGUIServer(self.fixQ, self.recvQ)
            self.recvThread = Thread(target=self.OnRecvQueue)
            self.recvThread.daemon = True
            self.recvThread.start()
            
            # create the dispatcher object to handle messages
            self.command_interface = SaviorCommandInterface.SaviorCommandInterface(self)

        self._display_windows = []
        # Create the video display
        for current_channel_index in range(self.n_channels):

            if self.matrox_frame_grabber.IsChannelEnabled(current_channel_index):


                channel_video_settings = {'channel_number' : current_channel_index,
                                          'channel_label'  : self.settings['image_acquisition_settings']['channel_labels'][current_channel_index]}

                channel_video_frame = VideoDisplay.VideoDisplayWindow(self.savior_panel,
                                                                      channel_video_settings,
                                                                      self.matrox_frame_grabber_event_generator,
                                                                      icon = self.savior_icon)
                self._display_windows.append(channel_video_frame)
                channel_video_frame.Bind(wx.EVT_CLOSE, self._OnVideoFrameClose)

##        # assume the videos are the same size
##        if len(self._display_windows) > 0:
##
##            video_window_width, video_window_height = self._display_windows[0].GetSize()
##            savior_width, savior_height = self.savior_panel.GetSize()
##
##            screen_width, screen_height = wx.GetDisplaySize()
##
##            screen_width -= savior_width
##
##            n_video_columns = screen_width / video_window_width
##            if n_video_columns < 1:
##                n_video_columns = 1
##
##            n_video_rows    = self.n_channels / n_video_columns
##            if n_video_rows < 1:
##                n_video_rows = 1
##
##            cur_x = 0
##            cur_y = 0
##            col_count = 0
##            for current_video_panel in range(len(self._display_windows)):
##                self._display_windows[current_video_panel].SetPosition((cur_x, cur_y))
##
##                if col_count >= n_video_columns - 1:
##                    col_count = 0
##                    cur_y += video_window_height
##                    cur_x = 0
##                else:
##                    col_count += 1
##                    cur_x += video_window_width

        # we have created the GUI
        self.initialized = True

        if SaviorHardwareConfiguration.gui_settings['launch_secondary_display']:

            self.savior_panel.OnNewSecondaryOpen(None)


    def GetVersion(sel):
        return version

    def _OnVideoFrameClose(self, event):

        obj = event.GetEventObject()
        for index in range(len(self._display_windows)):

            if obj == self._display_windows[index]:
                self._display_windows.pop(index)
                break

        event.Skip()

    def LaunchVideoDisplayWindw(self, channel_index):

        # see if the window is already opened
        for current_video_display in self._display_windows:
            if current_video_display.GetChannelIndex() == channel_index:
                current_video_display.SetFocus()
                return

        # build the frame if it doesn't exist
        if self.matrox_frame_grabber.IsChannelEnabled(channel_index):

            channel_video_settings = {'channel_number' : channel_index,
                                      'channel_label'  : self.settings['image_acquisition_settings']['channel_labels'][channel_index]}

            channel_video_frame = VideoDisplay.VideoDisplayWindow(self.savior_panel,
                                                                  channel_video_settings,
                                                                  self.matrox_frame_grabber_event_generator)
            self._display_windows.append(channel_video_frame)
            channel_video_frame.Bind(wx.EVT_CLOSE, self._OnVideoFrameClose)

    def OnKeyUp(self, event):
        
        """Doing nothing when a key pressed is up
        """

        event.Skip()

    def OnRecvQueue(self):
        while True:
            recvVal = self.recvQ.get()  # Block until we get something.
            # In this setup with our FixationGUI, we should only get key commands.
            if recvVal == "F4":
                keypress = wx.KeyEvent(wx.wxEVT_CHAR)
                keypress.m_keyCode = wx.WXK_F4
                self.OnKeyDown(keypress)

            # a fov was sent via the gui
            else:
                # remove parentheses and split the string for the two numbers
                fov = recvVal.strip('()')
                fov = fov.decode("utf-8").split()

                # get rid of comma behind first value
                fov[0] = fov[0].replace(',', '')

                # convert fov numbers to floats
                # if unicode has error line under it don't mess with it, it works on AO computers
                fov0 = float(unicode(fov[0]))
                fov1 = float(unicode(fov[1]))

                fovfinal = (fov0, fov1)

                # send fov to savior
                self.savior_panel.optical_scanners_control_panel.OnGUISetFOV(fovfinal)

    def OnKeyDown(self, event):
        """
        """

        # Note the arrow keys are bound in the optical scanners panel

        # function hot keys

        if not event.AltDown() and not event.ControlDown() and not event.ShiftDown():

            if event.GetKeyCode() == wx.WXK_F1:

                hot_key_text = 'Hot keys:\nF2 - Pause\nF3 - Play\nF4 - Record'

                wx.MessageBox(hot_key_text)

            elif event.GetKeyCode() == wx.WXK_F2:

                self.savior_panel.bottom_panel.OnStopButton(event = None)

            elif event.GetKeyCode() == wx.WXK_F3:

                self.savior_panel.bottom_panel.OnLiveButton(event = None)

            elif event.GetKeyCode() == wx.WXK_F4:

                self.savior_panel.bottom_panel.OnRecordButton(event = None)

            elif event.GetKeyCode() == wx.WXK_F5:
                self.savior_panel.optical_scanners_control_panel.ResetOffsets()
                pass

        event.Skip()
        
    def OnClose(self, event):
        """
        """
       
        # shut down the previous communication
        self.command_interface.CloseCommunicationThread()
        
        # if the synchronization was lost, stop the beeping thread
        if self.sync_loss_thread != None:
            self.warning_user_of_sync_loss = False

        #self.matrox_frame_grabber.StopEventDispatchPython()
        
        # clean up resources, we do the matrox
        # first so that we wont get a grab
        # error when we stop the signals
        self.matrox_frame_grabber.StopCapture()

        self._display_windows = []

        #self.matrox_frame_grabber.ReleasePythonCallbacks()
        self.matrox_frame_grabber.CloseMIL()

        self.signal_generator.OnClose(gui_display = True)
        
        if self.sync_loss_thread != None:
            self.sync_loss_thread.join()
            
        event.Skip()

    def OnMatroxStateChange(self, event = None):
        """
        """

        if self.matrox_frame_grabber != None:
            current_state = self.matrox_frame_grabber.GetCurrentState()

            if current_state == MatroxFramegrabber.LIVE:

                # if the syncronization was lost, stop the beebing thread
                if self.sync_loss_thread != None:
                    self.warning_user_of_sync_loss = False
                    self.sync_loss_thread.join()
                    self.sync_loss_thread = None
                    self.savior_panel.top_panel.SetBackgroundColour('default')
                    
            elif current_state == MatroxFramegrabber.STOPPED:
                pass

            elif current_state == MatroxFramegrabber.RECORDING:
                # just entered the recording state, beep to indicate the start of a movie
                self.OnGrabStart()

                current_movie_number = self.savior_panel.bottom_panel.GetCurrentMovieNumber()
                for current_display  in self._display_windows:
                    current_display.SetCurrentMovieNumber(current_movie_number)

        self.PauseExposureSignals()

        if event != None:
            event.Skip()

    def PauseExposureSignals(self):
        """
            This method pauses the exposure signals that have been selected
            to be off during paused video acquisition
        """
        if self.matrox_frame_grabber != None:
            current_state = self.matrox_frame_grabber.GetCurrentState()

            # copy the exposure settings to temporarily disable them
            temp_eposure_settings = copy.deepcopy(self.settings ['optical_scanners_settings']['exposure_settings'])

            if current_state == MatroxFramegrabber.STOPPED:

                # go through the exposure signals, find
                # the signals that are selected as off when
                # paused and disable those channels,
                # note we must also invert the active high setting
                # this is because when the exposure is disabled it keeps the signals
                # in the "on" position. I use this hack to invert what the signal generator thinks
                # is the "On" position so it actually turns the laser off when paused
                # TODO: make the changes to the video signal generator to make this cleaner
                #       probably include a new signal for turning laser on and off manually....
                for exp_key in temp_eposure_settings.keys():
                    if temp_eposure_settings[exp_key]['off_when_paused']:
                        temp_eposure_settings[exp_key]['active_high'] = not temp_eposure_settings[exp_key]['active_high']
                        temp_eposure_settings[exp_key]['enabled'] = False


            self.signal_generator.SetExposureSettings(temp_eposure_settings)    
        

    def OnGrabFinished(self, event = None):
        """
        """

        # we don't want the GUI to hang while the computer beeps so
        # I break this off onto its own thread        
        beeping_thread = threading.Thread(target = __MultipleBeeps__,
                                          args   = (2, 0.3, 325, 30),
                                          name = "grab finished beeping")
        beeping_thread.start()

        if event != None:
            event.Skip()

            
            
    def OnGrabStart(self, event = None):
        """
        """

        # we don't want the GUI to hang while the computer beeps so
        # I break this off onto its own thread        
        beeping_thread = threading.Thread(target = __MultipleBeeps__,
                                          args   = (1, 0.3, 325, 30),
                                          name = "grab started beeping")
        beeping_thread.start()

        if event != None:
            event.Skip()

    
    def OnMatroxGrabError(self, event = None):
        """
        """
    
        expected_fps = self.matrox_frame_grabber.GetFrameRate()
    
        self.savior_panel.bottom_panel.OnStopButton(None)
    
        # Make the GUI flash red and beep when syncronization is lost
        # make sure we don't launch two threads
        if self.sync_loss_thread == None:
            self.warning_user_of_sync_loss = True
            self.sync_loss_thread = threading.Thread(target = self.__SyncLossBeeping__,
                                                     name   = "grab error beeping thread")
            self.sync_loss_thread.start()
            
        self.savior_panel.top_panel.SetBackgroundColour('red')
    
        wx.MessageBox("Syncronization error, check resonant scanner!")

        # we should try to reallocate the signal generator
        self.signal_generator.RestartControlSignals()

        # Hide the stats for the video panel
        if self.display_frame != None:
            self.display_frame.HideStats()

        if event != None:
            event.Skip()


    
    def __SyncLossBeeping__(self):
        """
        """
        while self.warning_user_of_sync_loss:
            __MultipleBeeps__(1,   t_between_beeps_in_s = 0.3,
                      beep_frequency_in_Hz = 1000, beep_duration_in_ms  = 50)
                      
            time.sleep(1)



    def GetCurrentSettings(self):
        """
        """

        return self.savior_panel.GetCurrentSettings()



    def GetVideoFrame(self):
        """
        """

        return self.display_frame



if __name__ == '__main__':                          

    import DefaultSaviorSettings

    # temporary pause for debugging
    #a = raw_input('Press enter to continue')

        
    # starting the applicatioin
    my_savior = SaviorApp(clinical_version = True, initial_settings = DefaultSaviorSettings)
    
