import os
from flask import Response, flash, redirect


def yield_log(logf, redirect_to):
    if os.path.exists(logf):
        def generate():
            with open(logf, 'r') as f:
                lines = f.readlines()
            yield "<html>"
            if lines and not lines[-1].endswith("DONE!"):
                yield """
                        <center>
                        Process not done yet!
                        This page will automatically refresh in 5 seconds...<br>
                        <img src="/img/loading.gif"></img>
                        </center>
                        <script>
                        setTimeout(function() {
                          location.reload();
                        }, 5000);
                        </script>
                      """
            line = ""
            for line in reversed(lines):
                yield line + "</br>"
            yield "</html>"

        return Response(generate(), mimetype='text/html')
    flash('Log not created yet.')
    return redirect(redirect_to)


def clear_log(logf, redirect_to):
    if os.path.exists(logf):
        os.remove(logf)
    flash('Log cleared.')
    return redirect(redirect_to)