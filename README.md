# instagram reel sentiment analyzer

analyze sentiment of instagram reel comments

## setup

### python environment
1. create virtual env:
```bash
python -m venv venv
```

2. activate env:
```bash
windows: venv\Scripts\activate
mac/linux: source venv/bin/activate
```

3. install required packages:
```bash
pip install -r requirements.txt
```

## data pipeline
1. run server first:
```bash
python server.py
```

2. (login &) collect reel links:
```bash
python collect-reels.py
```

3. (login &) get reel data:
```bash
python collect-reel-data.py
```

4. analyze sentiment:
```bash
python vader-sentiment-analysis.py
```

5. create visualisation module (i.e. scatter graph):
```bash
python create-visualisation-module.py
```

## chrome extension
1. in chrome, go to: chrome://extensions/

2. enable "developer mode"

3. click "load unpacked"

4. select the chrome-extension/extension/ folder

5. run server
```bash
python server.py
```

6. go to instagram/explore and click "Analyze Reel" to start automatic analysis while scrolling