from flask import Flask, jsonify
from news_collector import collect_news

app = Flask(__name__)

@app.route('/api/news')
def get_news():
    news_list = collect_news()
    return jsonify(news_list)

if __name__ == '__main__':
    app.run(debug=True)
