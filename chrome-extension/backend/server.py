from flask import Flask, request, jsonify
from flask_cors import CORS
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# setup flask app
app = Flask(__name__)
CORS(app)  # allow cross-origin requests
analyzer = SentimentIntensityAnalyzer()

@app.route('/analyze', methods=['POST', 'OPTIONS'])
def analyze_sentiment():
    """handle sentiment analysis requests"""
    
    if request.method == 'OPTIONS':
        # handle preflight cors check
        response = jsonify({"status": "preflight"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    
    # get comments from request
    data = request.get_json()
    if not data or 'comments' not in data:
        return jsonify({"error": "no comments provided"}), 400
    
    comments = data['comments']
    if not isinstance(comments, list):
        return jsonify({"error": "comments must be an array"}), 400
    
    print("\n=== analyzing comments ===")
    compound_scores = []
    
    # analyze each comment
    for i, comment in enumerate(comments, 1):
        vs = analyzer.polarity_scores(comment)
        compound_scores.append(vs['compound'])
        print(f"comment {i}: {comment[:50]}{'...' if len(comment)>50 else ''}")
        print(f"  → compound: {vs['compound']:.4f} | pos: {vs['pos']:.2f} | neu: {vs['neu']:.2f} | neg: {vs['neg']:.2f}")
    
    # calculate averages
    avg_compound = sum(compound_scores)/len(compound_scores) if compound_scores else 0
    positive = len([s for s in compound_scores if s > 0.05])/len(compound_scores)
    neutral = len([s for s in compound_scores if -0.05 <= s <= 0.05])/len(compound_scores)
    negative = len([s for s in compound_scores if s < -0.05])/len(compound_scores)
    
    # prepare response
    response = jsonify({
        "compound": avg_compound,
        "positive": positive,
        "neutral": neutral,
        "negative": negative,
        "processed_comments": len(comments)
    })
    
    # add cors headers
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

if __name__ == '__main__':
    # start flask server
    app.run(host='0.0.0.0', port=5050, debug=True)