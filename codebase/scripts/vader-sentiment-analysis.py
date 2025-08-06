import json
import re
from statistics import mean
from pathlib import Path
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException

class VADERAnalyzer:
    def __init__(self):
        """set vader analyzer and initialize variables"""
        self.analyzer = SentimentIntensityAnalyzer()
        self.raw_data = None
        self.results = {}

    def clean_text(self, text):
        """pre-process raw textual data - makes for better vader analysis"""
        text = re.sub(r'@[^\s]+', '', text)  # remove account mentions
        text = re.sub(r'https?://\S+|www\.\S+', '', text)  # remove URLs
        text = ' '.join(text.split())  # normalise whitespace
        return text.strip()

    def is_english(self, text):
        """check if text is English"""
        if not text.strip():  # skip empty strings
            return False
            
        try:
            print("detecting")
            return detect(text) == 'en'
        except LangDetectException:
            return False  # skip if language detection fails
        except Exception as e:
            print(f"unexpected error detecting language: {e}")
            return False

    def load_data(self, input_file):
        """load reel data (i.e. comments and likes)"""
        with open(input_file, 'r') as f:
            self.raw_data = json.load(f)
        print(f"loaded data for {len(self.raw_data)} reels")

    def analyze_comments(self):
        """conduct vader analysis on comments, discard non-english text"""
        for reel_id, reel_data in self.raw_data.items():
            comments = reel_data['comments']
            analyzed_comments = []
            compound_scores = []
            
            for comment in comments:
                text = self.clean_text(comment['text'])
                
                # skip non-English comments
                if not self.is_english(text):
                    continue
                
                vs = self.analyzer.polarity_scores(text)
                            
                analyzed_comments.append({
                    'text': text,
                    'original_text': comment['text'],
                    'author': comment['author'],
                    'sentiment': {
                        'neg': vs['neg'],
                        'neu': vs['neu'],
                        'pos': vs['pos'],
                        'compound': vs['compound']
                    }
                })
                compound_scores.append(vs['compound'])
            
            if compound_scores:
                self.results[reel_id] = {
                    'url': reel_data['url'],
                    'likes': reel_data['likes'],
                    'comments_count': len(analyzed_comments),
                    'avg_sentiment': {
                        'neg': mean(c['sentiment']['neg'] for c in analyzed_comments),
                        'neu': mean(c['sentiment']['neu'] for c in analyzed_comments),
                        'pos': mean(c['sentiment']['pos'] for c in analyzed_comments),
                        'compound': mean(compound_scores)
                    },
                    'comments': analyzed_comments
                }
            else:
                # handle reels with only neutral or non-English comments
                self.results[reel_id] = {
                    'url': reel_data['url'],
                    'likes': reel_data['likes'],
                    'comments_count': 0,
                    'avg_sentiment': None, 
                    'comments': []
                }

    def save_results(self, output_file):
        """save results to json file"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"saved results to {output_file}")

    def run_analysis(self, input_file, output_file):
        """main function to run vader"""
        self.load_data(input_file)
        self.analyze_comments()
        self.save_results(output_file)


if __name__ == "__main__":
    analyzer = VADERAnalyzer()
    INPUT_DATA = "../data/demo-stuff/demo-reels-data.json"
    OUTPUT_RESULTS = "../data/demo-stuff/demo-vader-analysis-filtered.json"    # filtered out non-English comments
    
    if not Path(INPUT_DATA).exists():
        raise FileNotFoundError(f"input file not found: {INPUT_DATA}")
    
    analyzer.run_analysis(INPUT_DATA, OUTPUT_RESULTS)
    print("analysis complete!")