@echo off
rem Starts Fiji with biapy-ops' ops and scripts, from the checkouts.
rem
rem   start-fiji.bat C:\path\to\Fiji        (or set FIJI_DIR)
rem
rem fiji-skopkit (installed in that Fiji) finds scikit-ops through SKOP_CHECKOUT
rem and other op collections through SKOP_COLLECTIONS, so both are set here,
rem to the sibling checkouts: ..\..\scikit-ops and this repository. The scripts
rem in fiji\script_templates are packed into Fiji\jars\biapy-ops-templates.jar,
rem with the jar tool of the JDK Fiji bundles, so the Script Editor lists them
rem under Templates > biapy-ops, as fiji-skopkit's jar does its own. They are
rem also copied to Fiji\scripts\Plugins\biapy-ops, so they show in the Plugins
rem menu, next to the ops' own commands.
setlocal
set "FIJI=%~1"
if "%FIJI%"=="" set "FIJI=%FIJI_DIR%"
if "%FIJI%"=="" (
  echo Usage: start-fiji.bat C:\path\to\Fiji   ^(or set FIJI_DIR^)
  exit /b 1
)
for %%I in ("%~dp0..") do set "SKOP_COLLECTIONS=%%~fI"
for %%I in ("%~dp0..\..\scikit-ops") do set "SKOP_CHECKOUT=%%~fI"
if not exist "%SKOP_CHECKOUT%\envs" (
  echo No scikit-ops checkout at %SKOP_CHECKOUT%
  exit /b 1
)
xcopy /E /I /Y /Q "%~dp0script_templates\biapy-ops" "%FIJI%\scripts\Plugins\biapy-ops" >nul
set "JAR="
for /r "%FIJI%\java" %%J in (jar.exe) do if exist "%%J" set "JAR=%%J"
if "%JAR%"=="" (
  echo No jar.exe under %FIJI%\java, so the Script Editor templates are not installed
) else (
  "%JAR%" cf "%FIJI%\jars\biapy-ops-templates.jar" -C "%~dp0." script_templates
)
echo SKOP_CHECKOUT=%SKOP_CHECKOUT%
echo SKOP_COLLECTIONS=%SKOP_COLLECTIONS%
start "" "%FIJI%\fiji-windows-x64.exe" %2 %3 %4 %5 %6 %7 %8 %9
