import shlex
import time
import os
from docutils import core

try:
    from subprocess import check_output
except ImportError:
    import subprocess
    def check_output(cmd):
        return subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]


class templated(object):
    """
    Wrap the outout of a function with a string template
    """
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

    def __call__(self, func):
        def templated_func(*args, **kwargs):
            return self.head + func(*args, **kwargs) + self.tail
        return templated_func

class wsgify(object):
    """
    Wrap the outout of a function into a form of
    output fapws wsgi understands
    """
    def __init__(self, content_type):
        self.content_type = content_type

    def __call__(self, func):
        def wsgi_func(*args, **kwargs):
            start_response = args[2]
            start_response('200 OK', [('Content-Type', self.content_type)])
            return [func(args[0]), ]
        return wsgi_func

def run_command(command):
    """
    Run a shell command and return its output
    """
    try:
        return check_output(shlex.split(command))
    except:
        print "Command %s failed" % command
        return None


def sort_by_date(file_list):
    date_list = []
    for file in file_list:
        stats = os.stat(file)
        last_mod_date = time.localtime(stats[8])
        date_list.append((last_mod_date, file))
    date_list.sort()
    date_list.reverse()
    return [f[1] for f in date_list]


def reST_to_html(string):
    parts = core.publish_parts(
                                source=string,
                                writer_name='html',)
    return parts['body_pre_docinfo']+parts['fragment']

def get_git_info(clone_path):
    """
    Function to retrieve basic information about a cloned repo
    """
    with file(os.path.join(clone_path, '.git/logs/HEAD')) as f:
        latest_commit = list(f)[-1].split(' ')
        commit_hash = latest_commit[1][0:6]
        commit_time = latest_commit[5] + latest_commit[6].split("\t")[0]
        commit_message = " ".join(latest_commit[7:])
    return {
            "hash": commit_hash,
            "time": commit_time,
            "message": commit_message
           }

def yorn(question):
    """
    Convience function for yes or no questions
    """
    answer = raw_input("%s (y/N): " % question).lower()
    if answer == "y" or answer == "yes":
        return True
    if answer == "n" or answer == "no":
        return False
    else:
        return False


