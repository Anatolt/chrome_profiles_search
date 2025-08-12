@echo off
REM Быстрый запуск ChromeProfileLauncher без консольного окна (если установлен pythonw)
where pythonw >nul 2>nul
if %errorlevel%==0 (
  rem Проверяем, что tkinter установлен, иначе pythonw может молча упасть
  pythonw -c "import tkinter" >nul 2>nul
  if %errorlevel%==0 (
    start "" pythonw "%~dp0profiles.py"
    exit /b
  )
)

REM Если pythonw не найден, пробуем py лаунчер (может открыть консоль)
where py >nul 2>nul
if %errorlevel%==0 (
  py -c "import tkinter" >nul 2>nul
  if %errorlevel%==0 (
    start "" py "%~dp0profiles.py"
    exit /b
  ) else (
    echo Python найден, но не установлен модуль tkinter. Установите компонент Tcl/Tk для Python.
    pause
    exit /b 1
  )
)

REM Последняя попытка — python
where python >nul 2>nul
if %errorlevel%==0 (
  python -c "import tkinter" >nul 2>nul
  if %errorlevel%==0 (
    start "" python "%~dp0profiles.py"
    exit /b
  ) else (
    echo Python найден, но не установлен модуль tkinter. Установите компонент Tcl/Tk для Python.
    pause
    exit /b 1
  )
)

echo Не найден Python. Установите Python 3.x с опцией "Add Python to PATH".
pause
