# Based on https://www.roytuts.com/python-flask-file-upload-example/
import os
from flask import Flask, render_template, send_from_directory
from security.auth import bp as auth_bp
from routes.conversion import bp as conversion_bp

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024

app.register_blueprint(auth_bp, url_prefix="/auth")
app.register_blueprint(conversion_bp, url_prefix="/conversion")

img_dir = os.path.abspath(os.path.dirname(__file__) + '/img')


@app.route('/')
def view_home():
    return render_template('home.html')


@app.route('/img/<string:fname>')
def get_img(fname):
    fname = fname.strip('.')
    return send_from_directory(img_dir, fname)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, use_reloader=False, debug=False)