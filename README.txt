STOCKDASH MANUAL SETUP COMMANDS
===============================

STEP 1: INSTALL PYTHON BACKEND DEPENDENCIES
============================================
pip install flask
pip install flask-cors
pip install requests
pip install beautifulsoup4
pip install PyJWT
pip install bcrypt

STEP 2: INSTALL REACT FRONTEND DEPENDENCIES
===========================================
cd frontend
npm install
npm install ogl
npm install react-router-dom
cd ..

STEP 3: START BACKEND SERVER
============================
cd backend
python app.py

STEP 4: START FRONTEND SERVER (in new terminal/command prompt)
=============================================================
cd frontend
npm start

FINAL RESULT
============
Backend:  http://localhost:5000
Frontend: http://localhost:3000

TROUBLESHOOTING
===============
If pip fails, try:
pip install --user [package-name]

If npm fails, try:
npm cache clean --force
npm install

If Python not found:
Download from https://python.org

If npm not found:
Download Node.js from https://nodejs.org
