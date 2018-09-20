# importing Python libraries
import os, wx, time, threading, pickle, winsound, string, copy
import wx.lib.agw.flatnotebook as fnb
import wx.lib.newevent
import numpy as np
import wx.lib.agw.advancedsplash as AS
import scipy.io as sio
import zmq
import yaml
import ClinicalLiveStreamMathDisplay
import SteeringControlFrame
import NystagmusCorrectionWindow

# contains the local path for the savior fvile structure
import SaviorHardwareConfiguration

# Import the fixation GUI.
from wxFixGUI import wxFixationFrame
from multiprocessing import Process, Queue

# changing cwd so that we know where all of the files are.
os.chdir(SaviorHardwareConfiguration.local_path)

# TODO: implement shutter safety.

# importing home-made user interface modules
import wxSaviorTopPanel, wxSaviorImageAcquisitionPanel, VideoDisplay, \
       wxSaviorOpticalScannersPanel,\
       wxSaviorBottomPanel, wxTrackingFrameDisplay, wxSaviorSettingsFileGrid, \
       wxEventGenerator, SaviorCommandInterface,   \
       ParseDCFFile, IlluminationControlFrame, ClinicalExposureSettingsPanel,\
       wxSaviorExposureSignalsDialog

# importing hardware control modules
import MatroxFramegrabber, SignalGenerator

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
                       fixQ                                 = None,
                       software_configuration_dictionary    = None):
        """
        """

        self.software_configuration_dictionary = software_configuration_dictionary

        # grab a reference to the hardware control
        self.matrox_frame_grabber_event_generator = matrox_frame_grabber_event_generator

        if matrox_frame_grabber_event_generator != None:
            self.matrox_frame_grabber            = matrox_frame_grabber_event_generator.GetEventGenerator()
        else:
            self.matrox_frame_grabber            = None

        # bind the OnStateChange method
        self.matrox_frame_grabber_event_generator.BindWXEvent("state_changed", self.OnMatroxStateChanged)

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
                          "Savior - Clinical",
                          style = wx.DEFAULT_FRAME_STYLE ^(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))

        # setting the panel size
        main_panel_width                        = 700
        main_panel_height                       = 825
        self.SetClientSize((main_panel_width, main_panel_height))

        # setting the panel background and foreground colors
        self.SetBackgroundColour((50, 50, 50))
        self.SetForegroundColour('white')

        # Create the two queues we'll post to in order to pass messages to
        # the fixation GUI
        self.fixQ = fixQ

        # creating top panel
        self.top_panel                            = wxSaviorTopPanel.wxSaviorTopPanel(self,
                                                                                      matrox_frame_grabber_event_generator,
                                                                                    local_savior_path                    = SaviorHardwareConfiguration.local_path)

        # # creating middle panel, setting its size and colours
        # self.middle_panel                         = wx.Panel(self, -1)
        # self.middle_panel.SetClientSize((self.GetClientSize()[0], 950))
        # self.middle_panel.SetBackgroundColour(self.GetBackgroundColour())
        # self.middle_panel.SetForegroundColour(self.GetForegroundColour())

        # creating the image acquisition panel
        self.image_acquisition_control_panel      = wxSaviorImageAcquisitionPanel.\
                                                    wxSaviorImageAcquisitionPanel(
                                                    self,
                                                    initial_settings['clinical_version'],
                                                    initial_settings['image_acquisition_settings'],
                                                    self.matrox_frame_grabber_event_generator,
                                                    self.top_panel,
                                                    self.software_configuration_dictionary)

        self.exposure_panel                      = ClinicalExposureSettingsPanel.ClinicalExposureSettingsPanel(self,
                                                                                                               initial_settings['optical_scanners_settings'],
                                                                                                               self.signal_generator)

        # creating the optical scanners acquisition panel
        self.optical_scanners_control_panel       = wxSaviorOpticalScannersPanel.\
                                                    wxSaviorOpticalScannersPanel(
                                                    parent                                  = self,
                                                    initial_optical_scanners_settings       = initial_settings['optical_scanners_settings'],
                                                    initial_resolution_calculation_settings = initial_settings['image_resolution_calculation_settings'],
                                                    clinical_version_boolean                = initial_settings['clinical_version'],
                                                    signal_generator                        = self.signal_generator,
                                                    top_panel                               = self.top_panel,
                                                    software_configuration_dictionary       = self.software_configuration_dictionary)

        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        temp_image_acquisition_control_panel_size = self.image_acquisition_control_panel.GetClientSize()

        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        self.image_acquisition_control_panel.SetClientSize(temp_image_acquisition_control_panel_size)

        # creating bottom panel
        self.bottom_panel  = wxSaviorBottomPanel.wxSaviorBottomPanel(self,
                                                    bottom_panel_initial_settings,
                                                    local_savior_path = SaviorHardwareConfiguration.local_path,
                                                    matrox_frame_grabber_event_generator = self.matrox_frame_grabber_event_generator,
                                                    top_panel = self.top_panel)

        # This should not be required, but for whatever reason adding the
        # panels to the book changes their size to (0, 0)!!!!!
        temp_bottom_panel_size = self.bottom_panel.GetClientSize()

        vertical_space = (10, 10)

        # creating vertical sizer to split the frame vertically in three
        main_sizer             = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(self.top_panel, flag = wx.EXPAND)
        main_sizer.Add(wx.StaticLine(self), flag = wx.EXPAND)

        spacing_sizer = wx.BoxSizer(wx.HORIZONTAL)
        center_sizer = wx.BoxSizer(wx.VERTICAL)

        center_sizer.Add(self.optical_scanners_control_panel, flag = wx.EXPAND)
        center_sizer.AddSpacer(vertical_space)
        center_sizer.Add(wx.StaticLine(self), flag = wx.EXPAND, border = 4)
        center_sizer.AddSpacer(vertical_space)
        center_sizer.Add(self.exposure_panel, flag = wx.EXPAND)
        center_sizer.AddSpacer(vertical_space)
        center_sizer.Add(wx.StaticLine(self), flag = wx.EXPAND, border = 4)
        center_sizer.AddSpacer(vertical_space)
        center_sizer.Add(self.image_acquisition_control_panel)
        center_sizer.AddSpacer(vertical_space)

        spacing_sizer.AddSpacer((50, 10))
        spacing_sizer.Add(center_sizer, flag = wx.EXPAND)
        spacing_sizer.AddSpacer((50, 10))

        main_sizer.Add(spacing_sizer, flag = wx.EXPAND)

        main_sizer.Add(wx.StaticLine(self), flag = wx.EXPAND)
        main_sizer.Add(self.bottom_panel,   flag = wx.EXPAND)

        # # This should not be required, but for whatever reason adding the
        # # panels to the book changes their size to (0, 0)!!!!!
        # self.bottom_panel.SetClientSize(temp_bottom_panel_size)

        # resizing the frame
        self.SetSizer(main_sizer)

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
        secondary_display     = view_menu.Append(-1, "Secondary &display window")
        steer_display         = view_menu.Append(-1, "&Steering control")
        illumination_window   = view_menu.Append(-1, "Display &illumination options")
        exposure_option       = view_menu.Append(-1, "Display &exposure settings")

        # keep track of the auxiliary frames
        self.illumination_window          = None
        self.remote_control_frame         = None
        self._nystagmus_correction_window = None
        self._nystagmus_settings          = {}
        self._steer_control_window        = None
        self.exposure_frame               = None

        self.secondary_display_windows = []

        help_menu           = wx.Menu()
        help_menu.AppendSeparator()

        about_option        = help_menu.Append(-1, "&About")

        menu_bar            = wx.MenuBar()
        menu_bar.Append(file_menu, "File")
        menu_bar.Append(view_menu, "Open")
        menu_bar.Append(help_menu, "Help")
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.OnMenuExitClick,             exit_option)
        self.Bind(wx.EVT_MENU, self.OnMenuSaveClick,             save_option)
        self.Bind(wx.EVT_MENU, self.OnMenuLoadClick,             load_option)
        self.Bind(wx.EVT_MENU, self.OnMenuAboutClick,            about_option)
        self.Bind(wx.EVT_MENU, self.OnNewSecondaryOpen,          secondary_display)
        self.Bind(wx.EVT_MENU, self.OnOpenSteerControl,          steer_display)
        self.Bind(wx.EVT_MENU, self.OnExposureSettingsClick,     exposure_option)
        self.Bind(wx.EVT_MENU, self.OnIlluminationSettingsClick, illumination_window)

        # Get the display size and put this window in the top right side
        screen_resolution   = wx.GetDisplaySize()
        current_size        = self.GetSize()

        top_left_corner     = (screen_resolution[0] - current_size[0], 0)

        # placing the window on the top left corner of the monitor
        self.SetPosition(top_left_corner)

        # positioning the window almost on the top right corner of the screen
        screen_width, screen_height = wx.GetDisplaySize()
        window_width, window_height = self.GetSize()

        # the 5 pixel shift is because of the window border
        self.SetPosition(wx.Point(screen_width - window_width - 5, 5))

        # for current_expression in self.settings['secondary_display_settings']['default_expressions']:
        #
        #     secondary_display = ClinicalLiveStreamMathDisplay.LiveStreamMathDisplayFrame(self,
        #                                                                          default_expression = current_expression,
        #                                                                          frame_grabber      = self.matrox_frame_grabber,
        #                                                                          common_expressions = self.settings['secondary_display_settings']['common_expressions'])
        #
        #     secondary_display.Bind(wx.EVT_CLOSE, self.OnSecondaryWindowClose)
        #
        #     self.secondary_display_windows.append(secondary_display)


        # making the window visible
        self.Show()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnOpenSteerControl(self, event):

        if self._steer_control_window == None:
            self._steer_control_window = SteeringControlFrame.SteeringControlFrame(optical_scanners_panel = self.optical_scanners_control_panel,
                                                                                   parent      = self)

            # bind the on close event so we can keep track of the window
            self._steer_control_window.Bind(wx.EVT_CLOSE,
                                            self.OnSteerControlFrameClose,
                                            self._steer_control_window)

        else:
            # bringing to the top, even if minimized
            self._steer_control_window.SetFocus()
            self._steer_control_window.Iconize(False);

    def OnSteerControlFrameClose(self, event):

        self._steer_control_window = None

        event.Skip()

    def OnMatroxStateChanged(self, event):

        current_state = self.matrox_frame_grabber.GetCurrentState()


        if current_state == MatroxFramegrabber.RECORDING:
            movie_number = self.bottom_panel.GetCurrentMovieNumber()
            self.top_panel.SetCurrentMovieNumber(movie_number)

        event.Skip()

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
            self.fixQ.put((-1,'I''m never gonna dance again'))

        # close the secondary displays
        for current_display in self.secondary_display_windows:
            current_display.Close()
        self.secondary_display_windows = []

        event.Skip()

    def OnNewSecondaryOpen(self, event):

        if len(self.settings['secondary_display_settings']['default_expressions']) > 0:
            default = self.settings['secondary_display_settings']['default_expressions']

        secondary_display = ClinicalLiveStreamMathDisplay.LiveStreamMathDisplayFrame(self,
                                                                             default_expression = self.settings['secondary_display_settings']['default_expressions'][0],
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
                                                 self.settings['optical_scanners_settings']['exposure_settings'],
                                                 self.matrox_frame_grabber_event_generator,
                                                 self.signal_generator,
                                                 self.bottom_panel)
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
                        self.matrox_frame_grabber_event_generator)

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

        # additionally we don't want to change FOV settings


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
        info.Version     = str(wx.GetApp().GetVersion())
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
                     self.optical_scanners_control_panel.GetCurrentSettings())

        # add the bottom panel settings to the image_acquistion_settings dictionary
        settings[0].update(settings[1])

        configuration_settings = {'clinical_version'                      : self.settings['clinical_version'],
                                  'image_acquisition_settings'            : settings[0],
                                  'optical_scanners_settings'             : settings[2]['optical_scanners_settings'],
                                  'image_resolution_calculation_settings' : settings[2]['image_resolution_calculation_settings']}

        configuration_settings['image_acquisition_settings']['channel_labels']                    = self.settings['image_acquisition_settings']['channel_labels']
        configuration_settings['image_acquisition_settings']['DCF_file']                          = self.settings['image_acquisition_settings']['DCF_file']

        return configuration_settings

    def SetCurrentSettings(self, settings):

        # Section added by Robert Cooper 09/23/2013
        # Whenever the new settings are set, update the FOV size on the fixation GUI.
        # If the frame isn't spawned yet, don't attempt to set the FOV.
        if self.fixQ is not None:
            try:
                # 1 is for FOV changes
                self.fixQ.put((1, settings['optical_scanners_settings']['resonant_scanner_amplitude_in_deg'],
                              settings['optical_scanners_settings']['raster_scanner_amplitude_in_deg']), block=False, timeout=.5  )
            except:
                pass

        self.image_acquisition_control_panel.SetCurrentSettings(settings['image_acquisition_settings'])

        bottom_panel_initial_settings        =  {'n_frames_to_record'                        : settings['image_acquisition_settings']['n_frames_to_record']}

        self.secondary_display_settings = copy.deepcopy(settings['secondary_display_settings'])
        self.bottom_panel.SetCurrentSettings(bottom_panel_initial_settings)

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



