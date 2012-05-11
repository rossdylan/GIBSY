#!/usr/bin/python2.7

import fapws._evwsgi as evwsgi
import os
import json
from fapws import base
from daemon import Daemon
import utilities as util


DEFAULT_CONFIG = {
        "blog_title": "New Gibsy Blog",
        "git_repo": "path/to/git/repository",
        "git_clone": "path/to/clone/of/repo",
        "pid_path": "path/to/gibsy/pid",
        "host": "0.0.0.0",
        "port": "8080",
        "blog_url": "gibsy.awesome-sauce.com",
        "blog_desc": "Fuck yah Gibsy"}




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
        util.run_command("git pull origin master")
        os.chdir(current_dir)

    def run(self):
        from blog import Blog
        self.update()
        self.blog = Blog(self.config)
        evwsgi.start(self.config['host'], self.config['port'])
        evwsgi.set_base_module(base)
        self.loadWebPath()
        evwsgi.run()

def gibsy_main():
    import sys
    from installer import install
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

if __name__ == "__main__":
    gibsy_main()
