from multiprocessing import Process
from helpers.environment import DEBUGGING
from datetime import datetime
import traceback
import os


def start_processing(do_work, logf):
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return "DEBUG"
    else:
        with open(logf, 'a+') as f:
            ts = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            f.write("\n[%s] Started Processing.\n" %ts)

        if DEBUGGING:
            do_work()
        else:
            p = Process(target=do_work)
            p.start()


def create_worker(process_file, proc_args, prefix, logf):
    def do_work():
        try:
            for line in process_file(*proc_args):
                with open(logf, 'a+') as f:
                    ts = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                    f.write("[%s] %s\n" % (ts, line));

            success = True
        except Exception as ex:
            success = False
            with open(logf, 'a+') as f:
                ts = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                f.write("[%s][EXCEPTION]" % ts)
                f.write(repr(ex))
                traceback.print_exc()

        ts = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        with open(logf, 'a+') as f:
            if success:
                f.write("[%s] Files should appear in <a href='%s'>View Files</a><br>" % (ts, "/%s/proc/view" % prefix))
            else:
                f.write("[%s] !!!!!!!!!!!! Operation Failed !!!!!!!!!!!!!!!" % ts)

            f.write("[%s] DONE!" % ts)

    return do_work
