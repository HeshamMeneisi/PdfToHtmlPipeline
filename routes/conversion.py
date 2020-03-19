from processing.manager import start_processing, create_worker
import tempfile
from flask import Blueprint, send_from_directory, render_template, redirect, flash, Response
from upload.manager import upload_to
from helpers.functions import mkdir_p
from logs.logger import yield_log, clear_log
from files.manager import delete_file, view_files
from security.auth import ensure_secure
import os

from processors.conversion import process_file

prefix = __name__.split('.')[-1]

UPLOAD_FOLDER = os.path.abspath('./storage/uploads/' + prefix)
PROC_FOLDER = os.path.abspath('./storage/processed/' + prefix)
LOG_DIR = os.path.abspath('./storage/logs/' + prefix)
CACHE_DIR = os.path.abspath('./storage/cache/' + prefix)

bp = Blueprint(prefix, __name__, template_folder='templates')


for d in [UPLOAD_FOLDER, PROC_FOLDER, LOG_DIR, CACHE_DIR]:
    if not os.path.exists(d):
        mkdir_p(os.path.abspath(d))


@bp.before_request
def sec_pass():
    r = ensure_secure()
    if r is not None:
        return r


@bp.route('/proc/download/<string:fname>')
def dl_proc(fname):
    fname = fname.strip('.')
    return send_from_directory(PROC_FOLDER, fname)


@bp.route('/raw/download/<string:fname>')
def dl_raw(fname):
    fname = fname.strip('.')
    return send_from_directory(UPLOAD_FOLDER, fname)


@bp.route('/proc/del/<fname>')
def del_proc(fname):
    delete_file(PROC_FOLDER, fname)
    return redirect('/' + prefix + '/proc/view')


@bp.route('/raw/del/<fname>')
def del_raw(fname):
    delete_file(UPLOAD_FOLDER, fname)
    return redirect('/' + prefix + '/raw/view')


@bp.route('/proc/view')
def view_processed():
    return view_files(
        location=PROC_FOLDER,
        actions={
            "Download": '/' + prefix + "/proc/download/{file}",
            "Delete": '/' + prefix + "/proc/del/{file}"
        },
        title="View Processed - HTML",
        header="Processed Files (HTML)"
        )


@bp.route('/raw/view')
def view_raw():
    return view_files(
        location=UPLOAD_FOLDER,
        actions={
            "Download": '/' + prefix + "/raw/download/{file}",
            "Delete": '/' + prefix + "/raw/del/{file}",
            "Process": '/' + prefix + "/raw/process/{file}",
            "View Log": '/' + prefix + "/raw/log/view/{file}",
            "Clear Log": '/' + prefix + "/raw/log/clear/{file}"
        },
        title="View Raw - PDF",
        header="Raw Files (PDF)")


@bp.route('/raw/log/view/<fname>')
def view_log(fname):
    logf = os.path.join(LOG_DIR, fname + '.log')
    return yield_log(logf, '/' + prefix + '/raw/view')


@bp.route('/raw/log/clear/<fname>')
def del_log_file(fname):
    logf = os.path.join(LOG_DIR, fname + '.log')
    return clear_log(logf, '/'+prefix+'/raw/view')


@bp.route('/raw/process/<fname>')
def proc_raw(fname):
    logf = os.path.join(LOG_DIR, fname + '.log')
    do_work = create_worker(process_file, (os.path.join(UPLOAD_FOLDER, fname), PROC_FOLDER), prefix, logf)
    start_processing(do_work, logf)

    return redirect('/' + prefix + "/raw/log/view/" + fname)


@bp.route('/upload', methods=['POST'])
def upload_file():
    return upload_to(UPLOAD_FOLDER, ['zip', 'pdf'])


@bp.route('/upload')
def upload_form():
    return render_template('upload.html', title="Upload Raw - PDF", header="Upload Raw File (PDF)")