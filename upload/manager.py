from flask import request, redirect, flash
from werkzeug.utils import secure_filename
import os


def allowed_file(filename, allowed_ext):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_ext


def upload_to(dest, allowed_ext=None):
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected for uploading')
            return redirect(request.url)
        if file and (allowed_ext is None or allowed_file(file.filename, allowed_ext)):
            filename = secure_filename(file.filename)
            file.save(os.path.join(dest, filename))
            flash('File successfully uploaded')
            return redirect(request.url)
        else:
            flash('Allowed file types are ' + ','.join(allowed_ext))
            return redirect(request.url)
