#!/usr/bin/python2.7

import fapws._evwsgi as evwsgi
from docutils import core
import shlex
import os
import sys
import time
import json
import PyRSS2Gen as rss2
import datetime
import re
from fapws import base
from daemon import Daemon
try:
    from subprocess import check_output
except:
    import subprocess
    def check_output(cmd):
        return subprocess.Popen(cmd,stdout=subprocess.PIPE).communicate()[0]

DEFAULT_CONFIG = {
        "blog_title": "New Gibsy Blog",
        "git_repo": "path/to/git/repository",
        "git_clone": "path/to/clone/of/repo",
        "pid_path": "path/to/gibsy/pid",
        "host": "0.0.0.0",
        "port": "8080",
        "blog_url": "gibsy.awesome-sauce.com",
        "blog_desc": "Fuck yah Gibsy"}


"""
function decorators section
"""
TEMPLATE_HEAD = ""
TEMPLATE_HEAD += '<html>'
TEMPLATE_HEAD += '<link href="css" rel="stylesheet" type="text/css">'
TEMPLATE_HEAD += '<link rel="stylesheet" '
TEMPLATE_HEAD += 'href='
TEMPLATE_HEAD += '"http://twitter.github.com'
TEMPLATE_HEAD += '/bootstrap/1.4.0/bootstrap.min.css">'
TEMPLATE_TAIL = "</html>"

POST_TEMPLATE_HEAD = "<div class='row'><div class='span-two-thirds offset1'>"
POST_TEMPLATE_TAIL = "</div></div>"


class templated(object):
    """
    Wrap the output of a function with a template
    """
    def __init__(self, head, tail):
        self.head = head
        self.tail = tail

    def __call__(self, func):
        def templated_func(*args, **kwargs):
            return self.head + func(*args, **kwargs) + self.tail
        return templated_func


class wsgify(object):
    def __init__(self, content_type):
        self.content_type = content_type

    def __call__(self, func):
        def wsgi_func(*args, **kwargs):
            start_response = args[2]
            start_response('200 OK', [('Content-Type', self.content_type)])
            return [func(args[0]), ]
        return wsgi_func


"""
Utlity Functions
"""


def run_command(command):
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


"""Installer functions"""
def generate_git_hook(config_path):
    return "#!/bin/bash\ngibsy.py restart %s" % config_path

def install():
    cwd = os.getcwd()
    install_here = yorn("Install to current directory?")
    if install_here:
        install_path = cwd
    else:
        install_path = raw_input("Enter an install path; ")
    blog_name = raw_input("Enter a blog name: ")
    os.chdir(install_path)
    print "Creating Git Repository"
    git_repo = os.path.join(install_path,blog_name + ".git")
    os.mkdir(git_repo)
    os.chdir(git_repo)
    run_command("git init --bare")
    os.chdir(install_path)
    print "Cloning Git Repository"
    run_command("git clone %s" % git_repo)
    git_clone = os.path.join(install_path,blog_name)
    print "Creating Gibsy File Structure"
    os.chdir(git_clone)
    os.mkdir("posts")
    run_command("touch posts/first.post")
    config_path = os.path.join(git_clone, "gibsy.conf")
    git_hook = generate_git_hook(config_path)
    with open("gibsy.conf", "w") as f:
        DEFAULT_CONFIG.update({"git_repo": git_repo, "git_clone": git_clone, "pid_path": os.path.join(git_clone,"gibsy.pid")})
        f.write(json.dumps(DEFAULT_CONFIG))
    print "Commiting and pushing fle structure"
    run_command("git add posts/first.post gibsy.conf")
    run_command("git commit -m 'initial commit'")
    run_command("git push origin master")
    print "Creating git hook"
    os.chdir(git_repo)
    with open("hooks/post-receive","w") as f:
        f.write(git_hook)
    os.chdir(cwd)

"""Blog Data classes"""


class BlogPost(object):
    def __init__(self, path):
        self.post_path = path
        first_line = True
        self.body = []
        stats = os.stat(path)
        self.date = time.localtime(stats[8])
        self.title = "Default Post"
        with open(self.post_path, 'r') as f:
            for line in f:
                if first_line:
                    self.title = reST_to_html(line)
                    first_line = False
                else:
                    self.body.append(line)
        self.body = reST_to_html('\n'.join(self.body))

    def getWebPath(self):
        """
        Get the path used by the webserver to display this content
        """
        if "/" in self.post_path:
            return self.post_path.split("/")[-1]
        else:
            return self.post_path

    def getPostTitle(self):
        """Return the html for the title of this blog post"""
        return self.title

    @templated(POST_TEMPLATE_HEAD, POST_TEMPLATE_TAIL)
    def getPostBody(self):
        """Return the html for the post body"""
        return self.body

    def getFormattedPost(self):
        return ''.join(
                ['<a href="%s">' % self.getWebPath(),
                self.getPostTitle(),
                "</a><br />",
                self.getPostBody()
                ])

    def getRSSItem(self,url):
        return rss2.RSSItem(
                title=re.sub('<[^<]+?>', '', self.title),
                link=url + "/" + self.getWebPath(),
                description=' '.join([w for w in self.body.split(" ")[0:len(self.body) // 4]]),
                guid=rss2.Guid(url + "/" + self.getWebPath()),
                pubDate=datetime.datetime(*self.date[0:6]))

    @wsgify("text/html")
    @templated(TEMPLATE_HEAD, TEMPLATE_TAIL)
    def getPostPage(self):
        return str(self.getFormattedPost())


class Blog(object):
    def __init__(self, config):
        self.config = config
        self.git_repo = self.config['git_repo']
        self.git_clone = self.config['git_clone']
        self.blog_title = self.config['blog_title']

        self.posts = []
        self.posts_path = os.path.join(self.git_clone, "posts")

        self.pygments = run_command("pygmentize -S colorful -f html")
        post_listing = os.listdir(self.posts_path)
        post_files = [os.path.join(self.posts_path, f) for f in post_listing]
        post_files = sort_by_date(post_files)
        for post_file in post_files:
            self.posts.append(BlogPost(post_file))

    @wsgify("text/css")
    def getPygments(self):
        return self.pygments

    @wsgify("text/html")
    @templated(TEMPLATE_HEAD, TEMPLATE_TAIL)
    def getIndexPage(self):
        index = []
        index.append("<title>" + self.blog_title + "</title>")
        index.append('<a href="/"><h1>' + self.blog_title + "</h1></a>")
        index.append("<br />")
        index.append("<body><div class='row'><div class='span11' offset1'>")
        index.append("<br /><br />".join([post.getFormattedPost() for post in self.posts]))
        index.append("</div></div></body>")
        return str("\n".join(index))

    @wsgify("application/xml")
    def getRSSFeed(self):
        rss = rss2.RSS2(
                title=self.blog_title,
                link=self.config['blog_url'] + "/rss",
                description=self.config['blog_desc'],
                lastBuildDate=datetime.datetime.utcnow(),
                items=[p.getRSSItem(self.config['blog_url']) for p in self.posts])
        return rss.to_xml()


class Server(Daemon):

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = json.loads(open(self.config_path).read())
        Daemon.__init__(self, self.config['pid_path'])

    def loadWebPath(self):
        for post in self.blog.posts:
            evwsgi.wsgi_cb(("/%s" % post.getWebPath(), post.getPostPage))
        evwsgi.wsgi_cb(("/rss", self.blog.getRSSFeed))
        evwsgi.wsgi_cb(("/css", self.blog.getPygments))
        evwsgi.wsgi_cb(("", self.blog.getIndexPage))

    def update(self):
        current_dir = os.getcwd()
        os.chdir(self.config['git_clone'])
        run_command("git pull origin master")
        os.chdir(current_dir)

    def run(self):
        self.update()
        self.blog = Blog(self.config)
        evwsgi.start(self.config['host'], self.config['port'])
        evwsgi.set_base_module(base)
        self.loadWebPath()
        evwsgi.run()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        command = sys.argv[1]
        config_file = sys.argv[2]
        s = Server(config_file)
        if command == "start":
            s.start()
        elif command == "stop":
            s.stop()
        elif command == "restart":
            s.restart()
        elif command == "debug":
            s.run()
        elif command == "update":
            s.update()
    elif len(sys.argv) == 2:
        if sys.argv[1] == "install":
            install()
    else:
        print "gibsy: [update install start stop restart debug] [config_file]"
