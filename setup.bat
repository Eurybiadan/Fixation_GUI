set "thispath=%~dp0"
set thispath=%thispath:~0,-1%

echo Creating virtual environment in: %thispath%

REM Install virtualenv, if it doesnt' exist.
py -m pip install virtualenv
REM Install the virtual environment
py -m virtualenv "%thispath%\venv"

REM Activate our virtualenv, then install wxPython 4 and numpy.
"%thispath%\venv\Scripts\activate.bat" & py -m pip install wxPython & py -m pip install numpy & "%thispath%\venv\Scripts\deactivate.bat"