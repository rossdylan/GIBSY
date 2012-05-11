#!/usr/bin/python2.7

import fapws._evwsgi as evwsgi
import os
import json
from fapws import base
from daemon import Daemon

DEFAULT_CONFIG = {
        "blog_title": "New Gibsy Blog",
        "git_repo": "path/to/git/repository",
        "git_clone": "path/to/clone/of/repo",
        "pid_path": "path/to/gibsy/pid",
        "host": "0.0.0.0",
        "port": "8080",
        "blog_url": "gibsy.awesome-sauce.com",
        "blog_desc": "Fuck yah Gibsy"}


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

def gibsy_main():
    import sys
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
