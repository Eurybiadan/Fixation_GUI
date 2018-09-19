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

# current software version 
version    = "2.0"

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
from FixGUIProc import FixGUIServer
from multiprocessing import Process, Queue

# changing cwd so that we know where all of the files are.
os.chdir(SaviorHardwareConfiguration.local_path)

# TODO: implement shutter safety.

# importing home-made user interface modules
import wxSaviorTopPanel, wxSaviorImageAcquisitionPanel, wxVideoDisplayFrame, \
       wxSaviorOpticalScannersPanel, wxSaviorEyeTrackingPanel, \
       wxSaviorBottomPanel, wxTrackingFrameDisplay, wxSaviorSettingsFileGrid, \
       wxEventGenerator, SaviorCommandInterface,   \
       ParseDCFFile, wxSaviorExposureSignalsDialog, IlluminationControlFrame
       
# importing hardware control modules
import MatroxFramegrabber, SignalGenerator

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



###########################################################################    
#                         Main application class                          #
###########################################################################    

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
                                 'exposure_settings'                     : initial_settings.exposure_settings,
                                 'secondary_display_settings'            : initial_settings.secondary_display_settings}

        # initializing the hardware and GUI
        self.LoadConfiguration(settings)

        # Opening the settings file grid
        self.savior_panel.OnMenuLoadClick(None)
        
        # starting the main event loop
        self.MainLoop()      

    def LoadConfiguration(self, new_settings):
    
        """Updating the SLO and imaging acquisition settings. See the file
           SaviorSettings.pyw for an up to date example of the dictionary
           that is required here. 
        """
        
        # keeping an internal copy of the new settings
        self.settings                       = new_settings

        # The settings passed here will never contain the hardware information
        # Grabbing the stuff from the hardware configuration file
        self.settings['optical_scanners_settings'].update(  SaviorHardwareConfiguration.optical_scanners_settings  )
        self.settings['image_acquisition_settings'].update( SaviorHardwareConfiguration.image_acquisition_settings )
        self.settings['eye_tracking_settings'].update(      SaviorHardwareConfiguration.eye_tracking_settings)

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

            # wait for any previous frames to be processed
            self.matrox_frame_grabber.StopEventDispatchPython()

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
            self.matrox_frame_grabber.FlipVertical(  new_settings['image_acquisition_settings']['flip_displays_up_down'],    cur_channel_index)
            self.matrox_frame_grabber.FlipHorizontal(new_settings['image_acquisition_settings']['flip_displays_left_right'], cur_channel_index)

        # determining how fast we should update statistics on the display panel
        self.stats_update_rate_in_updates_per_second   = new_settings['image_acquisition_settings']['stats_update_rate_in_Hz']
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
            self.signal_generator.SetVoltages(self.settings ['optical_scanners_settings'])
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
            self.matrox_frame_grabber.SetIlluminationMode(current_channel, illumination_mode)

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
            self.savior_panel.SetCurrentSettings(new_settings)

            # update the video display
            self.display_frame.SetSettings(video_display_settings)
            
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
            
            # Create the two queues we'll post to in order to pass messages to
            # the fixation GUI
            self.fixQ = Queue(1)
            
            # creating application main frame 
            self.savior_panel  = SaviorMainPanel(new_settings,
                                                 self.LoadConfiguration,
                                                 self.savior_icon,   
                                                 self.matrox_frame_grabber_event_generator,
                                                 self.signal_generator,
                                                 self.fixQ)

            # update the savior GUI
            self.savior_panel.SetCurrentSettings(new_settings)

            # Create the video display
            self.display_frame = wxVideoDisplayFrame.VideoDisplayFrame(self.savior_panel, 
                                                                       'Savior Video Display', 
                                                                       video_display_settings, 
                                                                       (0, 0), 
                                                                       self.savior_icon,
                                                                       self.matrox_frame_grabber_event_generator)
            
        
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
            self.wxFixFrameProc = FixGUIServer(fixQ)
			
            # create the dispatcher object to handle messages
            self.command_interface = SaviorCommandInterface.SaviorCommandInterface(self)

        # update the top panel to reflect the new FOV
        self.savior_panel.top_panel.UpdateOpticalScannersAndImageSamplingDisplay(self.matrox_frame_grabber.GetVideoWidth(),
                                                                                 self.matrox_frame_grabber.GetVideoHeight(),
                                                                                 self.settings['optical_scanners_settings']['resonant_scanner_amplitude_in_deg'],
                                                                                 self.settings['optical_scanners_settings']['raster_scanner_amplitude_in_deg'])                                                                  

        # we have created the GUI
        self.initialized = True



    def OnKeyUp(self, event):
        
        """Doing nothing when a key pressed is up
        """

        event.Skip()

        
    def OnKeyDown(self, event):
        """
        """

        # Note the arrow keys are bound in the optical scanners panel

        # function hot keys
    
        if event.GetKeyCode() == wx.WXK_F1:
        
            wx.MessageBox('This will be a help dialog')
            
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

        self.matrox_frame_grabber.StopEventDispatchPython()
        
        # clean up resources, we do the matrox
        # first so that we wont get a grab
        # error when we stop the signals
        self.matrox_frame_grabber.StopCapture()
        
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
                # paused and disable those
                for exp_key in temp_eposure_settings.keys():
                    if temp_eposure_settings[exp_key]['off_when_paused']:
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



###########################################################################    
#                         GUI / application class                         #
###########################################################################

class SaviorMainPanel(wx.Frame):
    
    """This class implements an application for acquiring and recording
       images with a scanning laser ophthalmoscope.
    """

    def __init__(self, initial_settings,
                       load_new_configuration_function      = None,
                       savior_icon                          = None,
                       matrox_frame_grabber_event_generator = None,
                       signal_generator                     = None,
                       fixQ                                 = None):        
        """
        """

        # grab a reference to the hardware control
        self.matrox_frame_grabber_event_generator = matrox_frame_grabber_event_generator
        
        if matrox_frame_grabber_event_generator != None:
            self.matrox_frame_grabber            = matrox_frame_grabber_event_generator.GetEventGenerator()
        else:
            self.matrox_frame_grabber            = None

        self.signal_generator                    = signal_generator

        # Grab a reference to the initial settings
        self.settings                            = initial_settings
        
        # We only want one of these open at a time so keep track of it
        self.file_grid                           = None
        
        # The icon thata will go on the top left of the frame
        self.savior_icon                         = savior_icon
        
        self.load_new_configuration_function     = load_new_configuration_function

        bottom_panel_initial_settings            =  {'n_frames_to_record' : initial_settings['image_acquisition_settings']['n_frames_to_record']}
        
        # creating main window (in Python jargon: frame)
        wx.Frame.__init__(self, None, -1,
                          "Savior (v " + version + ")",
                          style = wx.DEFAULT_FRAME_STYLE ^(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        # setting the panel size
        main_panel_width                        = 760
        main_panel_height                       = 850
        self.SetClientSize((main_panel_width, main_panel_height))

        # setting the panel background and foreground colors
        self.SetBackgroundColour((50, 50, 50))
        self.SetForegroundColour('white')

        # Create the queues we'll post to in order to pass messages to
        # the fixation GUI
        self.fovQ = fixQ
        self.captQ = fixQ     

        # creating top panel
        self.top_panel                            = wxSaviorTopPanel.wxSaviorTopPanel(self,
                                                        local_savior_path                    = SaviorHardwareConfiguration.local_path)
                                                              
        # show/discard the discard blink panel as required
        self.top_panel.ShowDiscardBlinkIcon(initial_settings['image_acquisition_settings']['discard_blinks_boolean']) 

        # creating middle panel, setting its size and colours
        self.middle_panel                         = wx.Panel(self, -1)
        self.middle_panel.SetClientSize((self.GetClientSize()[0], 950))
        self.middle_panel.SetBackgroundColour(self.GetBackgroundColour())
        self.middle_panel.SetForegroundColour(self.GetForegroundColour())

        # creating the image acquisition panel
        self.image_acquisition_control_panel      = wxSaviorImageAcquisitionPanel.\
                                                    wxSaviorImageAcquisitionPanel(
                                                    self.middle_panel,
                                                    initial_settings['image_acquisition_settings'],
                                                    self.matrox_frame_grabber_event_generator,
                                                    self.top_panel)
        
        
                                      
        # creating the optical scanners acquisition panel
        self.optical_scanners_control_panel       = wxSaviorOpticalScannersPanel.\
                                                    wxSaviorOpticalScannersPanel(
                                                    parent                                  = self.middle_panel,
                                                    initial_optical_scanners_settings       = initial_settings['optical_scanners_settings'],
                                                    initial_resolution_calculation_settings = initial_settings['image_resolution_calculation_settings'],
                                                    clinical_version_boolean                = initial_settings['clinical_version'],
                                                    signal_generator                        = self.signal_generator,
                                                    top_panel                               = self.top_panel)
                                          
        self.eye_tracking_control_panel           = wxSaviorEyeTrackingPanel.\
                                                    wxSaviorEyeTrackingPanel(
                                                    self.middle_panel,
                                                    initial_settings['eye_tracking_settings'])
                                       
        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        temp_image_acquisition_control_panel_size = self.image_acquisition_control_panel.GetClientSize()

        # creating book with tabs
        self.book                                 = fnb.FlatNotebook(self.middle_panel, -1,         \
                                                                     agwStyle = fnb.FNB_NO_X_BUTTON \
                                                                           | fnb.FNB_NODRAG         \
                                                                           | fnb.FNB_SMART_TABS     \
                                                                           | fnb.FNB_NO_NAV_BUTTONS)
        # adding panels to the book
        self.book.AddPage(self.image_acquisition_control_panel, ' Image acquisition')
        self.book.AddPage(self.optical_scanners_control_panel,  ' Optical scanners')
        self.book.AddPage(self.eye_tracking_control_panel,      ' Eye tracking')

        # getting background and foreground colours from the parent panel,
        # note that FlatNotebook requires that all colours are passed as
        # wx.Colour, NOT tuples
        bg_colour = wx.Colour(self.GetBackgroundColour()[0], self.GetBackgroundColour()[1], self.GetBackgroundColour()[2], 255)
        fg_colour = wx.Colour(self.GetForegroundColour()[0], self.GetForegroundColour()[1], self.GetForegroundColour()[2], 255)

        self.book.SetTabAreaColour(         bg_colour)
        self.book.SetActiveTabColour(       bg_colour)
        self.book.SetBackgroundColour(      bg_colour)

        self.book.SetActiveTabTextColour(   fg_colour)
        self.book.SetForegroundColour(      fg_colour)
        self.book.SetNonActiveTabTextColour(fg_colour)


        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        self.image_acquisition_control_panel.SetClientSize(temp_image_acquisition_control_panel_size)

        # estimating the book size AFTER adding the panels
        max_width          = 0
        max_height         = 0

        for page_index in range(self.book.GetPageCount()):
            max_width      = max(max_width,  self.book.GetPage(page_index).GetClientSize()[0])
            max_height     = max(max_height, self.book.GetPage(page_index).GetClientSize()[1])

        # setting the book size to fit the largest panel
        desired_book_size  = (max(self.book.GetClientSize()[0],  max_width),
                              max(self.book.GetClientSize()[1], max_height))


        #self.book.Fit()
        self.book.SetClientSize(        desired_book_size)
        self.middle_panel.SetClientSize(desired_book_size)
        
        # creating bottom panel
        self.bottom_panel  = wxSaviorBottomPanel.wxSaviorBottomPanel(self,
                                                    bottom_panel_initial_settings,
                                                    local_savior_path = SaviorHardwareConfiguration.local_path,
                                                    matrox_frame_grabber_event_generator = self.matrox_frame_grabber_event_generator,
                                                    top_panel = self.top_panel)

        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        temp_bottom_panel_size = self.bottom_panel.GetClientSize()

        # creating vertical sizer to split the frame vertically in three
        main_sizer             = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.top_panel,      0, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        main_sizer.Add(self.middle_panel,   1, wx.EXPAND)
        main_sizer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        main_sizer.Add(self.bottom_panel,   0, wx.EXPAND)

        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        self.bottom_panel.SetClientSize(temp_bottom_panel_size)

        # resizing the frame
        self.SetSizer(main_sizer)
        main_sizer.SetDimension(0, 0, self.GetClientSize()[0], self.GetClientSize()[1])
        #self.Fit()

        self.SetIcon(self.savior_icon)
        
        
##        self.CreateMenuBar()
##        self.CreateRightClickMenu()
##        self.LayoutItems()
##
##        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGING, self.OnPageChanging)
##        self.Bind(fnb.EVT_FLATNOTEBOOK_PAGE_CHANGED, self.OnPageChanged)
##
##        self.Bind(wx.EVT_UPDATE_UI, self.OnDropDownArrowUI, id=MENU_USE_DROP_ARROW_BUTTON)
##        self.Bind(wx.EVT_UPDATE_UI, self.OnHideNavigatisUI, id=MENU_HIDE_NAV_BUTTONS)
##        self.Bind(wx.EVT_UPDATE_UI, self.OnAllowForeignDndUI, id=MENU_ALLOW_FOREIGN_DND)


        ###################################################################
        ##                        Creating menus                         ##
        ###################################################################
        
        file_menu           = wx.Menu()
        file_menu.AppendSeparator()
        save_option         = file_menu.Append(-1, "&Save Current Configuration")
        load_option         = file_menu.Append(-1, "&Load Configuration")
        exit_option         = file_menu.Append(-1, "&Exit")

        # menu for selecting windows to be displayed
        view_menu             = wx.Menu()
        tracking_option       = view_menu.Append(-1, "Display &tracking frame")
        exposure_option       = view_menu.Append(-1, "Display &exposure settings")
        illumination_window   = view_menu.Append(-1, "Display &illumination options")
        secondary_display     = view_menu.Append(-1, "Open &secondary display window")
        nystagmus_control     = view_menu.Append(-1, "Open &nystagmus compensation display window")

        # keep track of the auxiliary frames
        self.exposure_frame               = None
        self.illumination_window          = None
        self.remote_control_frame         = None
        self._nystagmus_correction_window = None
        self._nystagmus_settings          = {}
        
        self.secondary_display_windows = []
        
        help_menu           = wx.Menu()
        help_menu.AppendSeparator()

        about_option        = help_menu.Append(-1, "&About")

        menu_bar            = wx.MenuBar()
        menu_bar.Append(file_menu, "File")
        menu_bar.Append(view_menu, "View")
        menu_bar.Append(help_menu, "Help")
        self.SetMenuBar(menu_bar)
        
        self.Bind(wx.EVT_MENU, self.OnMenuExitClick,             exit_option)
        self.Bind(wx.EVT_MENU, self.OnMenuSaveClick,             save_option)
        self.Bind(wx.EVT_MENU, self.OnMenuLoadClick,             load_option)
        self.Bind(wx.EVT_MENU, self.OnMenuAboutClick,            about_option)
        self.Bind(wx.EVT_MENU, self.OnExposureSettingsClick,     exposure_option)
        self.Bind(wx.EVT_MENU, self.OnIlluminationSettingsClick, illumination_window)
        self.Bind(wx.EVT_MENU, self.OnNewSecondaryOpen,          secondary_display)
        self.Bind(wx.EVT_MENU, self.OnNystagmusControl,          nystagmus_control)
        # Get the display size and put this window in the top right side
        screen_resolution   = wx.GetDisplaySize()
        current_size        = self.GetSize()
        
        top_left_corner     = (screen_resolution[0] - current_size[0], 0)
       
        # placing the window on the top left corner of the monitor
        self.SetPosition(top_left_corner)

        # eye tracking is always disabled by default
        self.top_panel.ShowEyeTrackingIcon(False)


        # positioning the window almost on the top right corner of the screen
        screen_width, screen_height = wx.GetDisplaySize()
        window_width, window_height = self.GetSize()

        # the 5 pixel shift is because of the window border
        self.SetPosition(wx.Point(screen_width - window_width - 5, 5))

        # making the window visible
        self.Show()
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
    def OnNystagmusControl(self, event):
    
        if self._nystagmus_correction_window == None:
        
            scanner_scaling_value = self.settings['optical_scanners_settings']['slow_scanner_calibration_scaling_factor']
        
            self._nystagmus_correction_window = NystagmusCorrectionWindow.NystagmusCorrectionWindow(self, 
                                                                                                    scanner_scaling_value, 
                                                                                                    self.signal_generator ,
                                                                                                    self._nystagmus_settings )
            self._nystagmus_correction_window.Bind(wx.EVT_CLOSE, self.OnNystagmusWindowClose)
    
        event.Skip()
        
    def OnNystagmusWindowClose(self, event):
    
        self._nystagmus_settings = self._nystagmus_correction_window.GetNystagmusSettings()
    
        self._nystagmus_correction_window = None
    
        event.Skip()
        
    def OnClose(self, event):
        
        if SaviorHardwareConfiguration.enable_fixation_gui:
            self.captQ.put(-1)
            
        # close the secondary displays
        for current_display in self.secondary_display_windows:
            current_display.Close()
        self.secondary_display_windows = []
    
        event.Skip()
        
    def OnNewSecondaryOpen(self, event):
    
        secondary_display = LiveStreamMathDisplay.LiveStreamMathDisplayFrame(self, 
                                                                             default_expression = "display_buffer = channel_0", 
                                                                             frame_grabber      = self.matrox_frame_grabber,
                                                                             common_expressions = self.secondary_display_settings['common_expressions'])
                                                                             
        secondary_display.Bind(wx.EVT_CLOSE, self.OnSecondaryWindowClose)
    
        self.secondary_display_windows.append(secondary_display)
    
        # dont skip the event? it fires twice for some reason?
        #event.Skip()
        
    def OnSecondaryWindowClose(self, event):
    
        window = event.GetEventObject()
        
        if self.secondary_display_windows.count(window) > 0:
            self.secondary_display_windows.pop(self.secondary_display_windows.index(window))
    
        event.Skip()
        
    def OnIlluminationSettingsClick(self, event):

        if self.illumination_window == None:
            self.illumination_window = IlluminationControlFrame.IlluminationControlFrame(self,
                                                 self.settings['optical_scanners_settings']['illumination_settings'],
                                                 self.matrox_frame_grabber,
                                                 self.signal_generator)
            self.illumination_window.Bind(wx.EVT_CLOSE, self.OnIlluminationWindowClose)

        else:
            self.illumination_window.SetFocus()

        event.Skip()

    def OnIlluminationWindowClose(self, event):

        self.illumination_window = None
        event.Skip()
        
    def OnExposureSettingsClick(self, event):

        if self.exposure_frame == None:
            self.exposure_frame = wxSaviorExposureSignalsDialog.wxSaviorExposureSignalsDialog(self,
                        self.settings['optical_scanners_settings']['exposure_settings'],
                        self.signal_generator,
                        self.matrox_frame_grabber_event_generator,
                        wx.GetApp().GetVideoFrame())

            self.exposure_frame.Bind(wx.EVT_CLOSE, self.OnExposureFrameClose)
        
        event.Skip()

    def OnExposureFrameClose(self, event):

        self.exposure_frame = None

        event.Skip()
        
     
    def OnMenuSaveClick(self, event):

        configuration_settings = self.GetCurrentSettings()
    
        # Get a file name from the user
        file_dialog   = wx.FileDialog(self,
                                      message       = "Choose a savior settings file",
                                      defaultDir    = os.getcwd(), 
                                      defaultFile   = "",
                                      wildcard      = "Savior setings file (*_savior_settings.py)|*_savior_settings.py",
                                      style         = wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)

        # Show dialog and retrieve user response
        if file_dialog.ShowModal() == wx.ID_OK:            

            destination_file = file_dialog.GetPath()
            
            file_dialog.Destroy()
            
            # loading Savior settings template file
            settings_template_file_name = 'SaviorSettingsFileTemplate.py'
            file_object                 = open(settings_template_file_name, 'r')
            settings_template_text      = file_object.readlines()
            file_object.close()

            n_lines                     = len(settings_template_text)

            # Consolidating the settings into one dictionary
            data_dictionary = {}
            data_dictionary.update(configuration_settings['optical_scanners_settings'])
            data_dictionary.update(configuration_settings['image_acquisition_settings'])
            data_dictionary.update(configuration_settings['image_resolution_calculation_settings'])
            data_dictionary.update(configuration_settings['eye_tracking_settings'])

            # adding a few things that are not stored by any page
            data_dictionary['exposure_settings']            = self.settings['optical_scanners_settings']['exposure_settings']
            data_dictionary['n_lines_per_strip']            = self.settings['image_acquisition_settings']['n_lines_per_strip']
            data_dictionary['n_lines_between_strip_starts'] = self.settings['image_acquisition_settings']['n_lines_between_strip_starts']

            # iterating through every line
            for line_index in range(n_lines):

                # going through all of the items in the configuration
                # and seeing if any of them belong in the template file
                for field, value in data_dictionary.items():

                    # formatting the key so that it matches what is in the template file
                    formatted_field_name = '{' + field + '}' 
                    
                    if string.find(settings_template_text[line_index], formatted_field_name)> -1:
                        
                        # putting the data in the text
                        if type(value) == str:
                            settings_template_text[line_index] = string.replace (settings_template_text[line_index],
                                                                                 formatted_field_name,
                                                                                 '\'' + str(value) + '\'')
                        else:                                                     
                            settings_template_text[line_index] = string.replace (settings_template_text[line_index],
                                                                                 formatted_field_name,
                                                                                 str(value))
                        
            # saving settings file

            if destination_file[(len(destination_file)-3):len(destination_file)].lower() == '.py':
                destination_file = destination_file[0:len(destination_file)-3]
                
            destination_file            = destination_file + '_savior_settings.py'
            
            file_object                 = open(destination_file, 'w')
            file_object.writelines(settings_template_text)
            file_object.close()

    def FormatSettings(self, settings_module):
    
        settings       = {'clinical_version'                      : self.settings['clinical_version'],
                          'optical_scanners_settings'             : settings_module.optical_scanners_settings,    
                          'image_resolution_calculation_settings' : settings_module.image_resolution_calculation_settings,
                          'image_acquisition_settings'            : settings_module.image_acquisition_settings,
                          'eye_tracking_settings'                 : settings_module.eye_tracking_settings,
                          'secondary_display_settings'            : settings_module.secondary_display_settings}


        # We would like the destination folders to stay the same so we will just add the original
        # ones to this structure
        current_settings = self.GetCurrentSettings()
        
        formatted_file_list = []
        for cur_file_index in range(len(current_settings['image_acquisition_settings']['destination_folders'])):

            if len(current_settings['image_acquisition_settings']['current_file_names'][cur_file_index]) > 0:
                formatted_file_list.append(current_settings['image_acquisition_settings']['destination_folders'][cur_file_index]\
                                           + '\\' + current_settings['image_acquisition_settings']['current_file_names'][cur_file_index])
            else:
                formatted_file_list.append(current_settings['image_acquisition_settings']['destination_folders'][cur_file_index])

        settings['image_acquisition_settings']['destination_folders'] = formatted_file_list
        
        if self.load_new_configuration_function != None:
            self.load_new_configuration_function(settings)


            
    def OnMenuLoadClick(self, event):
    
        # We only want one file grid open at a time so
        # if it is already open just give it focus
        if self.file_grid == None:
            # Launch the settings grid to select an input file
            self.file_grid = wxSaviorSettingsFileGrid.wxSaviorSettingsFileGrid(self,
                                        SaviorHardwareConfiguration.local_path + '\settings files',
                                        self.FormatSettings,
                                        self.OnFileGridClose,
                                        savior_icon = self.savior_icon)
            
            self.file_grid.Bind(wx.EVT_CLOSE, self.OnFileGridClose, self.file_grid)
            
            # setting the position to the bottom left of the screen
            monitor_resolution   = wx.GetDisplaySize()
            grid_size            = self.file_grid.GetSize()
            
            # the extra hard coded value is the height of the start menue
            pos = (0, monitor_resolution[1] - grid_size[1] - 30)
            self.file_grid.SetPosition(pos)
            
            self.file_grid.Show(True)            
        else:
            self.file_grid.SetFocus()

    def OnFileGridClose(self, event = None):
        self.file_grid = None
        
        if event != None:
            event.Skip()
            
    def OnMenuAboutClick(self, event):

        """This function shows an about window with copyrights, license and
           developers info.
        """
        
        # First we create and fill the info object
        info             = wx.AboutDialogInfo()
        info.Name        = "Savior"
        info.Version     = version
        info.Copyright   = "(C) 2010-2011 The University of Rochester, " +\
                           "all rights reserved.\n\n" +\
                           "(C) 2012 Medical College of Wisconsin, " +\
                           "all rights reserved.\n"
        info.Description = "Developed with the support of the Research to " +\
                           "Prevent Blindness Career Development Award to " +\
                           "Alfredo Dubra and the Catalyst for a Cure II "  +\
                           "from the Glaucoma Research Foundation"
        info.Developers  = ["Zachary Harvey (zgh7555@gmail.com)",
                            "Alfredo Dubra  (adubra@mcw.edu)"]

        info.License     = ""

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
        
        
    def OnMenuExitClick(self, event):
        
        self.Close()

    
##    def OnMenuHelpKnownBugsClick(self, event):
##        
##        """This function shows a list of the bugs known to date.
##        """
##
##        # I do not like this implementation because it a MS-DOS-type shell
##        #import os
##        #os.system('notepad.exe ' + './TsunamiWave Known Bugs.txt')
##
##        # reading file
##        f   = open('./documentation/TsunamiWave Known Bugs.txt', 'r')
##        msg = f.read()
##        f.close()
##
##        # creating and displaying modal dialog 
##        import wx.lib.dialogs
##        dlg = wx.lib.dialogs.ScrolledMessageDialog(self, msg, "TsunamiWave Known Bugs")
##        dlg.ShowModal()
##        
##
##
##    def OnMenuHelpManualClick(self, event):
##        
##        """This function should link to the corresponding manual.
##        """
##
##        import os
##        os.startfile ('./documentation/TsunamiWaveManual.doc')
##
##

    def GetCurrentSettings(self):
        
        settings =  (self.image_acquisition_control_panel.GetCurrentSettings(),  \
                     self.bottom_panel.GetCurrentSettings(),                     \
                     self.optical_scanners_control_panel.GetCurrentSettings(),   \
                     self.eye_tracking_control_panel.GetCurrentSettings())
        
        # add the bottom panel settings to the image_acquistion_settings dictionary
        settings[0].update(settings[1])
        
        # the dewarping matrix would be to much to save to file
        settings[3].pop('desinusoiding_matrix', None)
        
        configuration_settings = {'clinical_version'                      : self.settings['clinical_version'],
                                  'image_acquisition_settings'            : settings[0], 
                                  'optical_scanners_settings'             : settings[2]['optical_scanners_settings'],
                                  'image_resolution_calculation_settings' : settings[2]['image_resolution_calculation_settings'],
                                  'eye_tracking_settings'                 : settings[3]}
                                  
        
        # Removing the desinusoiding matrix as this is stored in the dewarping file
        configuration_settings['eye_tracking_settings'].pop('horizontal_warping', None)
        
        configuration_settings['image_acquisition_settings']['channel_labels']                    = self.settings['image_acquisition_settings']['channel_labels']
        configuration_settings['image_acquisition_settings']['DCF_file']                          = self.settings['image_acquisition_settings']['DCF_file']

        return configuration_settings
        
    def SetCurrentSettings(self, settings):

        # Section added by Robert Cooper 09/23/2013
        # Whenever the new settings are set, update the FOV size on the fixation GUI.
        # If the frame isn't spawned yet, don't attempt to set the FOV.
        if self.fovQ is not None:
            try:
                self.fovQ.put((1, settings['optical_scanners_settings']['resonant_scanner_amplitude_in_deg'], 
                              settings['optical_scanners_settings']['raster_scanner_amplitude_in_deg']), block=False, timeout=.5  )
            except:
                pass
    
        self.image_acquisition_control_panel.SetCurrentSettings(settings['image_acquisition_settings'])
        
        bottom_panel_initial_settings        =  {'n_frames_to_record'                        : settings['image_acquisition_settings']['n_frames_to_record']}
        
        self.secondary_display_settings = copy.deepcopy(settings['secondary_display_settings'])
        self.bottom_panel.SetCurrentSettings(bottom_panel_initial_settings)
        self.optical_scanners_control_panel.SetCurrentSettings(settings['optical_scanners_settings'], settings['image_resolution_calculation_settings'])
        self.eye_tracking_control_panel.SetCurrentSettings(settings['eye_tracking_settings'])

        # close the exposure panel if it is open
        if self.exposure_frame != None:
            self.exposure_frame.Close()

        # close the illumination dialog if it is open
        if self.illumination_window != None:
            self.illumination_window.Close()
            self.illumination_window = None
            
        # # close the secondary displays
        # for current_display in self.secondary_display_windows:
            # current_display.Close()
  
        # self.secondary_display_windows = []
            
        # # Open new secondary displays with the default expressions from configuration file
        # for current_expression in settings['secondary_display_settings']['default_expressions']:
        
            # secondary_display = LiveStreamMathDisplay.LiveStreamMathDisplayFrame(self, 
                                                                                 # default_expression = current_expression, 
                                                                                 # frame_grabber      = self.matrox_frame_grabber,
                                                                                 # common_expressions = \
                                                                                    # settings['secondary_display_settings']['common_expressions'])
                                                                                 
            # secondary_display.Bind(wx.EVT_CLOSE, self.OnSecondaryWindowClose)
            # self.secondary_display_windows.append(secondary_display) 
            

          
if __name__ == '__main__':                          

    import DefaultSaviorSettings

    # temporary pause for debugging
    #a = raw_input('Press enter to continue')

        
    # starting the applicatioin
    my_savior = SaviorApp(clinical_version = False, initial_settings = DefaultSaviorSettings)
    
