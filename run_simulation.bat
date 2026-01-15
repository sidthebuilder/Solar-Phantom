@echo off
echo ==========================================
echo SOLAR PHANTOM: Unified Simulation Pipeline
echo ==========================================

echo.
echo [1/3] Running Optimization (Designing the Drone)...
echo ---------------------------------------------------
python optimize.py
if %ERRORLEVEL% NEQ 0 (
    echo Error: Optimization failed. Please check if Python and dependencies are installed.
    pause
    exit /b
)

echo.
echo [2/3] Analyzing Year-Round Survival...
echo --------------------------------------
python analysis_annual.py
if %ERRORLEVEL% NEQ 0 (
    echo Error: Annual analysis failed.
    pause
    exit /b
)

echo.
echo [3/3] Generating Technology Roadmap...
echo --------------------------------------
python analysis_enterprise.py

echo.
echo ==========================================
echo SUCCESS: All simulations completed.
echo check 'design_specs.json' for the generated configuration.
echo ==========================================
pause
