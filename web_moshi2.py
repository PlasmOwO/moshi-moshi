from flask import Flask, send_from_directory, jsonify

app = Flask(__name__, static_url_path='', static_folder='.')

@app.route('/')
def root():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/get-transcribe-url')
def get_transcribe_url():
    return jsonify({"url": "ws://13.38.29.146:8500/transcribe"})

if __name__ == '__main__':
    app.run(port=3000)