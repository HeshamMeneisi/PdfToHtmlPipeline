import os
from flask import flash, render_template


def delete_file(location, fname):
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return "DEBUG"
    else:
        fname = fname.strip('.')
        os.remove(os.path.join(location, fname))
        flash('File %s deleted.' % fname)
        
        
def view_files(location, actions, title, header):
    files = []
    for file in os.listdir(location):
        sz = os.path.getsize(os.path.join(location, file))
        files.append((file, "%.2f MB" % (sz / 1024 / 1024), actions))
    return render_template('files.html', files=files, title=title, header=header)