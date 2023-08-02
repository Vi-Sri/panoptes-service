from flask import Flask, request
from multiprocessing import Queue, Process
from panoptes import Panoptes
from flask import jsonify

app = Flask(__name__)

panoptes = Panoptes()

# This is not fully implemented yet
@app.route('/add_video', methods=["POST"])
def add_video():
    vid_json = request.get_json()
    path = vid_json["path"]
    panoptes.add_video(path)
    return jsonify(dict(response=200))


@app.route('/search/<query>')
def search(query):
    query_results = panoptes.search(query)
    return jsonify(query_results)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
