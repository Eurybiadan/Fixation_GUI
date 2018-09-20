# Fixation_GUI - A simple fixation target driver.

This software provides an easy-to-use interface to drive secondary-monitor fixation systems (projectors, screens) for Ophthalmic devices. 

Fixation_GUI uses a socket-based interface to recieve notifications that an image has been acquired, or other aspects of imaging have been changed: e.g. the field of view of the instrument has been adjusted.


## General Usage:
__IMPORTANT NOTE: for Savior users, skip to Savior Installation Instructions below__
### Requirements:
1. Python 3.x (Note: tested on 3.6 & 3.7)
2. wxPython 4.x
3. numpy 1.15
4. Visual C++ Redistributable for Visual Studio 2015 (x86/x64)

### Running Instructions:
* Make sure the fixationgui folder is on your python path.
* Run wxFixGUI.py

## Savior Usage:
__These instructions apply to the latest (2016) version of Savior__
### Requirements:
1. Python 3.x (Note: tested on 3.6 & 3.7)
2. Visual C++ Redistributable for Visual Studio 2015 (x86/x64)

### Installation:
1. Run setup.bat (this will create a virtual 3.7 environment)
2. **IMPORTANT**-Create backup copies of:
    * Savior.pyw
    * SaviorClinicalPanel.pyw
    * wxSaviorBottomPanel.py
    * wxSaviorTopPanel.py
3. Copy the contents of ..\Fixation_GUI\pre_modified_server_side_scripts\ to your Savior folder.
4. ???
5. Profit!

# Enjoy! And please, acknowledge me if you use this software!
