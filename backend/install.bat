@echo off
echo ============================================
echo  Meeting AI Platform - Install Dependencies
echo ============================================
echo.

echo Step 1: Uninstalling conflicting packages...
pip uninstall sentence-transformers transformers torch torchvision torchaudio -y 2>nul

echo.
echo Step 2: Installing all dependencies...
pip install -r requirements.txt

echo.
echo Step 3: Installing TextBlob corpora...
python -m textblob.download_corpora

echo.
echo ============================================
echo  Done! Now run: uvicorn app.main:app --reload
echo ============================================
pause
