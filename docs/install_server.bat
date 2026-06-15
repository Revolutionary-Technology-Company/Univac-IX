mkdir ..\docs
(
echo @echo off
echo echo [INSTALLER] Mounting UNIVAC-IX Server into persistent Windows Service registries...
echo net session ^>nul 2^>^&1
echo if %%errorlevel%% neq 0 (
echo     echo Installation Fault: Elevated Administrator privileges required.
echo     exit /b 1
echo )
echo mkdir C:\univac_core
echo copy dist\main.exe C:\univac_core\univac_core_server.exe
echo copy config.yaml C:\univac_core\config.yaml
echo sc create univac_core binPath= "C:\univac_core\univac_core_server.exe listen-server --config C:\univac_core\config.yaml" start= auto
echo sc start univac_core
echo echo [SUCCESS] UNIVAC-IX Windows Service configured. Automatic system boot startup active.
) > ..\docs\install_server.bat
