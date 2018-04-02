@REM Call script with argument x32 or x64 to specify platform. Optional 2nd argument is the release number, e.g. 123.456
@REM

SETLOCAL ENABLEDELAYEDEXPANSION

@REM enable the platform specific compiler and python executable

set MYPLATFORM=%1

IF DEFINED MYPLATFORM (
IF %MYPLATFORM% == x32 (
  call "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\vcvars32.bat"
  set PYTHONEXE=D:\Python27\python.exe
)

IF %MYPLATFORM% == x64 (
  call "C:\Program Files (x86)\Microsoft Visual Studio 9.0\VC\bin\vcvars64.bat"
  @REM set PYTHONEXE=C:\Python27_64\python.exe
  set PYTHONEXE=D:\Python27\python.exe
)
)

@REM                  Platform specific compiler and python executable now set
mkdir %MYPLATFORM%
cd %MYPLATFORM%

%PYTHONEXE% -c "import time; print '-' + str((int((time.time() - 1404950400) / (24*60*60))))" > buildnumber.txt
SET /p BUILDNUMBER= < buildnumber.txt
%PYTHONEXE% -c "import time; print 'dev-' + str((int((time.time() - 1404950400) / (24*60*60))))" > version.txt

SET RELEASENUMBER=%2
IF DEFINED RELEASENUMBER (
  SET CCTBXVERSION=!RELEASENUMBER!!BUILDNUMBER!
) ELSE (
  SET CCTBXVERSION=dev!BUILDNUMBER!
)

title Bootstrap %CCTBXVERSION% on %MYPLATFORM%

@REM mkdir %CCTBXVERSION%
@REM cd %CCTBXVERSION%
mkdir Current
del *.log
cd Current

@echo %DATE% %TIME% > ..\build%CCTBXVERSION%-%MYPLATFORM%.log

@REM                           get latest bootstrap.py file
set GETBOOTSTRAP=%3
IF DEFINED GETBOOTSTRAP (
   @echo Get bootstrap.py | mtee /+ ..\build%CCTBXVERSION%-%MYPLATFORM%.log
   ( curl https://raw.githubusercontent.com/cctbx/cctbx_project/master/libtbx/auto_build/bootstrap.py > bootstrap.py ) 2>&1 ^
   | mtee /+ ..\build%CCTBXVERSION%-%MYPLATFORM%.log
)

@REM   with no flags bootstrap defaults to doing cleanup, hot, update, base and build stages
title Bootstrap %CCTBXVERSION% on %MYPLATFORM%  build
@echo %DATE% %TIME% >> ..\build%CCTBXVERSION%-%MYPLATFORM%.log
%PYTHONEXE% bootstrap.py --builder=cctbx --nproc=10  2>&1 ^
 | mtee /+ ..\build%CCTBXVERSION%-%MYPLATFORM%.log
IF ERRORLEVEL 1 (
  GOTO Makesummary
)
@echo %DATE% %TIME% | mtee /+ ..\build%CCTBXVERSION%-%MYPLATFORM%.log

@REM                             run tests
title Bootstrap %CCTBXVERSION% on %MYPLATFORM% tests
@echo %DATE% %TIME% > ..\tests%CCTBXVERSION%-%MYPLATFORM%.log
%PYTHONEXE% bootstrap.py --builder=cctbx --nproc=10 tests 2>&1 ^
 | mtee /+ ..\tests%CCTBXVERSION%-%MYPLATFORM%.log
IF ERRORLEVEL 1 (
  GOTO Makesummary
)
@echo %DATE% %TIME% | mtee /+ ..\tests%CCTBXVERSION%-%MYPLATFORM%.log

@REM                            create installer
title Bootstrap %CCTBXVERSION% on %MYPLATFORM% create_installer
@echo %DATE% %TIME% > ..\CreateInstaller%CCTBXVERSION%-%MYPLATFORM%.log
call build\bin\libtbx.create_installer.bat --binary --version %CCTBXVERSION% ^
 --install_script modules\cctbx_project\libtbx\auto_build\plus_installer.py ^
 --dist_dir dist\%CCTBXVERSION% tmp/cctbx-installer-%CCTBXVERSION%-win7vc90 2>&1 ^
  | mtee /+ ..\CreateInstaller%CCTBXVERSION%-%MYPLATFORM%.log
IF ERRORLEVEL 1 (
  GOTO Makesummary
)
@echo %DATE% %TIME% | mtee /+ ..\CreateInstaller%CCTBXVERSION%-%MYPLATFORM%.log

:Makesummary
@echo %CCTBXVERSION%-%MYPLATFORM% > ..\summary.log
%PYTHONEXE% -c "lines = open('..\\build%CCTBXVERSION%-%MYPLATFORM%.log','r').readlines(); lastlines = lines[(len(lines) - 5): ]; print ''.join(lastlines); " >> ..\summary.log
%PYTHONEXE% -c "lines = open('..\\tests%CCTBXVERSION%-%MYPLATFORM%.log','r').readlines(); lastlines = lines[(len(lines) - 5): ]; print ''.join(lastlines); " >> ..\summary.log
%PYTHONEXE% -c "lines = open('..\\CreateInstaller%CCTBXVERSION%-%MYPLATFORM%.log','r').readlines(); lastlines = lines[(len(lines) - 20): ]; print ''.join(lastlines); " >> ..\summary.log

REM print concatenated summary of logfiles in a message box
type ..\summary.log | msg %USERNAME% /time:86400

@ENDLOCAL
EXIT