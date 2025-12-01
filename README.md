AI DESKTOP DETECTOR – MULTI-MODEL IMAGE ANALYSIS SYSTEM
------------------------------------------------------------

This project is a complete end-to-end multi-model image detection system built as a desktop application using PyQt6.  
It supports multiple YOLO models, runs multi-model inference, logs results into Excel, annotates images, and provides a full CI/CD pipeline with automated builds.

This README explains how to set up, run, develop, test, package, and deploy the project.

------------------------------------------------------------
1. FEATURES
------------------------------------------------------------

• Multi-model YOLO detection (fire, textile, panel, custom models)
• Configurable model list (easy to add/remove models)
• PyQt6 desktop GUI
• Batch image processing
• Annotated image previews
• Excel logging (results.xlsx)
• Threaded inference (no UI freeze)
• CI/CD: GitHub Actions workflow
• Unit tests (pytest)
• PyInstaller packaging to standalone EXE or Linux/Mac binary
• NSIS installer script included
• Dockerfile for command-line inference mode

------------------------------------------------------------
2. PROJECT STRUCTURE
------------------------------------------------------------

ai-desktop-detector/
    main.py
    detection_core.py
    setup_structure.py
    requirements.txt
    requirements-dev.txt
    models/
    uploads/
    static/results/
    inference/
        detector.py
        commenter.py
    utils/
        viz.py
    tests/
        test_detector.py
        test_commenter.py
    .github/workflows/
        ci-cd.yml
    main.spec
    Dockerfile
    installer.nsi
    README.txt

------------------------------------------------------------
3. INSTALLATION (DEVELOPMENT SETUP)
------------------------------------------------------------

Step 1: Create virtual environment  
    python -m venv .venv  
    Windows: .venv\Scripts\activate  
    Linux/Mac: source .venv/bin/activate  

Step 2: Install project dependencies  
    pip install --upgrade pip  
    pip install -r requirements.txt  
    pip install -r requirements-dev.txt  

Step 3: Place your model files  
Put your .pt files into the models/ folder.  
Ensure their names match the MODEL_CONFIG list inside inference/detector.py.

------------------------------------------------------------
4. RUNNING THE DESKTOP APP
------------------------------------------------------------

From the project root:

    python main.py

The application UI will launch with:  
• Image preview  
• Model selection checkboxes  
• Single/multi file selection  
• Logs and status window  

Annotated images are saved into:  
    static/results/

Excel results are saved to:  
    static/results/results.xlsx

------------------------------------------------------------
5. PACKAGING INTO EXE (WINDOWS)
------------------------------------------------------------

Install PyInstaller:

    pip install pyinstaller

Option A: One-file executable:

    pyinstaller --noconfirm --onefile --windowed --add-data "static;static" --add-data "models;models" main.py

Option B: Using the main.spec file:

    pyinstaller --noconfirm main.spec

The generated EXE will be inside the dist/ folder.

------------------------------------------------------------
6. PACKAGING FOR MAC/LINUX
------------------------------------------------------------

Use the same pyinstaller command, but replace semicolon with colon:

    --add-data "static:static"
    --add-data "models:models"

Example:

    pyinstaller --onefile --windowed --add-data "static:static" --add-data "models:models" main.py

The binary will be inside dist/.

------------------------------------------------------------
7. INSTALLER CREATION (WINDOWS – NSIS)
------------------------------------------------------------

Install NSIS (Nullsoft Scriptable Install System).  
Then run:

    makensis installer.nsi

This will generate a setup.exe installer containing the PyInstaller build.

------------------------------------------------------------
8. RUNNING UNIT TESTS
------------------------------------------------------------

Use pytest:

    pytest -q

Tests included:  
• Model loading  
• Comment generator  
• Additional tests can be added under tests/

------------------------------------------------------------
9. CONTINUOUS INTEGRATION / CONTINUOUS DEPLOYMENT
------------------------------------------------------------

GitHub Actions workflow included at:

    .github/workflows/ci-cd.yml

It performs:  
• Code checkout  
• Dependency installation  
• Linting  
• Unit tests  
• Building executables for Windows, Linux, and macOS  
• Uploading built artifacts for download

Triggered automatically on:  
• Push to main  
• Pull requests  
• Manual trigger

------------------------------------------------------------
10. ADDING NEW MODELS
------------------------------------------------------------

To add a new YOLO model:  
1. Place .pt file in models/  
2. Open inference/detector.py  
3. Add new entry to MODEL_CONFIG:  
   {"name": "newmodel", "path": "models/newmodel.pt", "class_name": "your-class"}  

4. The GUI will automatically show a checkbox for this model  
5. The model will be included in inference  
6. Comments will be included in generate_comments()

------------------------------------------------------------
11. DOCKER MODE (OPTIONAL)
------------------------------------------------------------

If you want a headless inference API version, edit Dockerfile and add a FastAPI/Flask service file:

    docker build -t ai-detector .
    docker run -p 8000:8000 ai-detector

------------------------------------------------------------
12. TROUBLESHOOTING
------------------------------------------------------------

Q: My EXE crashes when loading models.  
A: Ensure .pt models are included in PyInstaller build. Check the --add-data paths.

Q: Annotated images not visible.  
A: Check static/results permissions or broken install path after packaging.

Q: CI build fails due to large models.  
A: Prefer downloading models from a private URL at build time.

------------------------------------------------------------
13. AUTHOR / SUPPORT
------------------------------------------------------------

This project supports:  
• Multi-model YOLO inference  
• PyQt6 UI  
• CI/CD  
• Packaging  
• Deployment  

For further additions (auto-updater, cloud model hosting, advanced GUI), request additional modules.

------------------------------------------------------------

END OF README  
------------------------------------------------------------
