#!/usr/bin/python2.7

import fapws._evwsgi as evwsgi
import markdown
import shlex
import os
import time
import json
from fapws import base
from daemon import Daemon
from subprocess import check_output

"""
function decorators section
"""
TEMPLATE_HEAD = ""
TEMPLATE_HEAD += '<html>'
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

"""Blog Data classes"""


class BlogPost(object):
    def __init__(self, path):
        self.post_path = path
        first_line = True
        self.body = []
        with open(self.post_path, 'r') as f:
            for line in f:
                if first_line:
                    self.title = markdown.markdown(line)
                    first_line = False
                else:
                    self.body.append(line)
        self.body = markdown.markdown('\n'.join(self.body),
                                    output_format='html5')

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

    @wsgify("text/html")
    @templated(TEMPLATE_HEAD, TEMPLATE_TAIL)
    def getPostPage(self):
        return str(self.getFormattedPost())


class Blog(object):
    def __init__(self, git_repo, git_clone, blog_title):
        self.git_repo = git_repo
        self.git_clone = git_clone
        self.blog_title = blog_title
        self.posts = []
        self.posts_path = os.path.join(self.git_clone, "posts")
        post_listing = os.listdir(self.posts_path)
        post_files = [os.path.join(self.posts_path, f) for f in post_listing]
        post_files = sort_by_date(post_files)
        for post_file in post_files:
            self.posts.append(BlogPost(post_file))

    @wsgify("text/html")
    @templated(TEMPLATE_HEAD, TEMPLATE_TAIL)
    def getIndexPage(self):
        index = []
        index.append('<a href="/"><h1>' + self.blog_title + "</h1></a>")
        index.append("<br />")
        index.append("<body><div class='row'><div class='span11' offset1'>")
        index.append("<br /><br />".join([post.getFormattedPost() for post in self.posts]))
        index.append("</div></div></body>")
        return str("\n".join(index))


class Server(Daemon):
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = json.loads(open(self.config_path).read())
        Daemon.__init__(self, self.config['pid_path'])

    def loadWebPath(self):
        for post in self.blog.posts:
            evwsgi.wsgi_cb(("/%s" % post.getWebPath(), post.getPostPage))
        evwsgi.wsgi_cb(("", self.blog.getIndexPage))

    def run(self):
        #current_dir = os.getcwd()
        #os.chdir(self.config['git_clone'])
        #run_command("git pull origin master")
        #os.chdir(current_dir)
        self.blog = Blog(self.config['git_repo'], self.config['git_clone'], self.config['title'])
        evwsgi.start(self.config['host'], self.config['port'])
        evwsgi.set_base_module(base)
        self.loadWebPath()
        evwsgi.run()

if __name__ == "__main__":
    s = Server("/home/posiden/Projects/gibsy_test/meta.conf")
    s.run()
