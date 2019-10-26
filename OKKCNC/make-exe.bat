pip2 install pyinstaller
pip2 install --upgrade setuptools
pyinstaller --onefile --distpath . --hidden-import tkinter --paths lib;plugins;controllers --icon bCNC.ico --name OKKCNC __main__.py
pause
