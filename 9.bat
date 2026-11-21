rem pyinstaller --noconfirm --onefile --windowed  --icon=icon.ico --add-data "icon.ico;." QRCodeDecoder.py
rem  D:\Program Files\Python310\Lib\site-packages\pyzbar
rem D:/Program Files/Python310/Lib/site-packages/pyzbar/

rem pyinstaller --noconfirm --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --add-binary "D:/Program Files/Python310/Lib/site-packages/pyzbar/libiconv.dll;pyzbar" QRCodeDecoder.py

pyinstaller --noconfirm --onefile --windowed --icon=icon.ico --add-data "icon.ico;." --add-binary "D:\Program Files\Python310\Lib\site-packages\pyzbar\libiconv.dll;pyzbar" --add-binary "D:\Program Files\Python310\Lib\site-packages\pyzbar\libzbar-64.dll;pyzbar" QRCodeDecoder.py
