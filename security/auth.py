from flask import make_response, render_template, request, Blueprint, redirect, flash
from cryptography.fernet import Fernet
from config.token import TOKEN

bp = Blueprint('auth', __name__, template_folder='templates')


@bp.route('/submit', methods=['POST'])
def authorize():
    user_token = request.form['token']
    if verify_token(user_token, False):
        target = request.cookies.get('auth_redirect')
        if not target:
            target = '/'
        return create_store_token_resp(target)

    flash("Invalid token.")
    return redirect('/')


def ensure_secure():
    user_token = request.cookies.get('token')

    if verify_token(user_token):
        return None
    else:
        resp = make_response(render_template('auth.html'))
        resp.set_cookie('auth_redirect', request.url)
        return resp


def verify_token(token, encrypted=True):
    if not token:
        return False

    if encrypted:
        f = Fernet(TOKEN)
        token = f.decrypt(token.encode('ASCII'))
        if token == TOKEN:
            return True
    else:
        if token == TOKEN.decode('utf8'):
            return True

    return False


def create_store_token_resp(target):
    f = Fernet(TOKEN)
    resp = make_response(redirect(target))
    resp.set_cookie('token', f.encrypt(TOKEN))
    return resp
