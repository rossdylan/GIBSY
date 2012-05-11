import os
import utilities as util
import json


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
    install_here = util.yorn("Install to current directory?")
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
    util.run_command("git init --bare")
    os.chdir(install_path)
    print "Cloning Git Repository"
    util.run_command("git clone %s" % git_repo)
    git_clone = os.path.join(install_path,blog_name)
    print "Creating Gibsy File Structure"
    os.chdir(git_clone)
    os.mkdir("posts")
    util.run_command("touch posts/first.post")
    config_path = os.path.join(git_clone, "gibsy.conf")
    git_hook = generate_git_hook(config_path)
    with open("gibsy.conf", "w") as f:
        DEFAULT_CONFIG.update({"git_repo": git_repo, "git_clone": git_clone, "pid_path": os.path.join(git_clone,"gibsy.pid")})
        f.write(json.dumps(DEFAULT_CONFIG))
    print "Commiting and pushing fle structure"
    util.run_command("git add posts/first.post gibsy.conf")
    util.run_command("git commit -m 'initial commit'")
    util.run_command("git push origin master")
    print "Creating git hook"
    os.chdir(git_repo)
    with open("hooks/post-receive","w") as f:
        f.write(git_hook)
    os.chdir(cwd)


