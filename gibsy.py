#!/usr/bin/python2

from subprocess import check_output
import shlex
import os
import os.path
import fapws._evwsgi as evwsgi
from fapws import base
import time
import sys
from daemon import Daemon
import PyRSS2Gen
import datetime

def runCommand(command):
    """
    Run a single command
    """
    return check_output(shlex.split(command))

def touch(filename):
    """
    Create a new empty file
    """
    runCommand("touch %s" % filename)

def commitDirectoryStructure(blogPath,gitPath):
    """
    Add the Directory Structure to the git repo
        git remote add origin <currentuser>@localhost:<gitPath>
        git add -a (Add all the things)
        git commit -m "Directory Creation"
        git push origin master
    """
    baseDir = os.getcwd()
    os.chdir(blogPath)
    runCommand("git init")
    runCommand("git remote add origin %s" % gitPath)
    runCommand("git add -A")
    runCommand("git commit -m 'Created base Directories'")
    runCommand("git push origin master")
    os.chdir(baseDir)

def createGitHookScript(gitDir,blogDir):
    parentDir = os.path.join(blogDir,"../")
    script = "#!/bin/bash\ncd %s\npython2 gibsy.py stop %s %s\nGIT_DIR=%s\ngit pull\npython2 gibsy.py start %s %s" % (parentDir,blogDir,gitDir,gitDir,blogDir,gitDir)
    touch(os.path.join(gitDir,"hooks/post-receive"))
    runCommand("chmod +x %s" % os.path.join(gitDir,"hooks/post-receive"))
    f = open(os.path.join(gitDir,"hooks/post-receive"),'w')
    f.write(script)
    f.close()

def createFileStrucutre(blogname):
    """
    Generate the file/directory structure for the blogging system
    <blogname>.git
        -All the git shits go here
    <blogname>
        -meta.conf #This holds data like site title, and other... things...
        in json.
        -Posts
            -All dem posts go here.txt
    """
    #Generate paths for blog, git, and posts
    blogDir = os.path.join(os.getcwd(),blogname)
    postsDir = os.path.join(blogDir,"posts")
    gitDir = os.path.join(os.getcwd(),"%s.git" % blogname)

    #Create all the things
    print "Create Directory Structure"
    os.mkdir(blogDir)
    os.mkdir(postsDir)
    touch(os.path.join(blogDir,"meta.conf"))
    touch(os.path.join(postsDir,"first.post"))
    print "Generating Git Repository"
    generateGitRepo(gitDir)

    #Commit/push all the things
    print "Commiting Directory structure to git"
    commitDirectoryStructure(blogDir,gitDir)
    createGitHookScript(gitDir,blogDir)

def generateGitRepo(gitPath):
    """
    Create a new git repository
    """
    prevPath = os.getcwd()
    os.mkdir(gitPath)
    os.chdir(gitPath)
    runCommand("git init --bare")
    os.chdir(prevPath)

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

def install():
    """
    Install Gibsy to the current directory
    """
    if yorn("Install gibsy to %s?" % os.getcwd()):
        blogName = raw_input("Enter a blog name: ").strip()
        createFileStrucutre(blogName)
    else:
        print "Good Bye"
        exit()
"""
End of all the install shits
Lets Do blog shits now!
"""
def getDataFromFile(filename):
    """
    Abstract that reading away
    """
    f = open(filename)
    data = f.read()
    f.close()
    return data

class post(object):
    """
    Hold all that post-y goodness, class holds single posts
    """
    def __init__(self,title,body,filename):
        """
        Initialize a post
        """
        self.filename = filename
        self.title = title
        self.body = body
    def wsgiCallback(self,environ, start_response):
        start_response('200 OK', [('ContentType', 'text/html')])
        body = "<br />".join(self.body.split("\n"))
        return ["<h1> " + self.title + "</h1><br />" + "<p>" + body + "</p>"]
    def getRSSItem(self,url):
        return PyRSS2Gen.RSSItem(
                title=self.title,
                link=url+"/"+self.filename,
                description=' '.join([w for w in self.body.split(" ")[0:len(self.body)//3]]),
                guid = PyRSS2Gen.Guid(url+"/"+self.filename))
    def __str__(self):
        """
        Return a html formmated string representation of a post
        """
        body = "<br />".join(self.body.split("\n"))
        return '<h2><a href="/%s">' % self.filename + self.title + "</a></h2><br /><p>"+body+"</p>"

class blog(object):
    """
    Hold all data for the blog
        -posts
        -meta
        -paths for things....
    """
    def __init__(self,blogPath):
        self.blogPath = blogPath
        self.postsPath = os.path.join(blogPath,"posts")
        self.meta = {}
        self.posts = []
    def generateRSSXML(self):
        rss = PyRSS2Gen.RSS2(title=self.meta['title']+" Feed",
                link=self.meta['blogurl']+"/rss",
                description=self.meta['blogdesc'],
                lastBuildDate = datetime.datetime.utcnow(),
                items=[p.getRSSItem(self.meta['blogurl']) for p in self.posts])
        return rss.to_xml()
    def pullFromGit(self):
        """
        Update the blog from the git repo
        """
        currentDir = os.getcwd()
        os.chdir(self.blogPath)
        #print "export GIT_DIR=%s" % os.path.join(os.getcwd(),".git")
        #runCommand("export GIT_DIR=%s" % os.path.join(os.getcwd(),".git"))
        
        runCommand("git pull origin master")
        os.chdir(currentDir)
    def sortByDate(self,filesList):
        """
        Sort files in descending order of most recently modified
        """
        dateList = []
        for file in filesList:
            stats = os.stat(file)
            lastModDate = time.localtime(stats[8])
            dateList.append((lastModDate,file))
        dateList.sort()
        dateList.reverse()
        return [f[1] for f in dateList]
    
    def loadPosts(self):
        """
        Load all the posts in the posts directory
        """
        dirList = os.listdir(self.postsPath)
        postFileList = [os.path.join(self.postsPath,f) for f in dirList if f.endswith(".post")]
        postFileList = self.sortByDate(postFileList)
        lePosts = []
        for postFile in postFileList:
            postData = getDataFromFile(postFile)
            lines = postData.split("\n")
            title = lines[0]
            body = "\n".join(lines[1:])
            lePosts.append(post(title,body,postFile.split("/")[-1].split(".")[0]))
            print "loaded post %s" % postFile.split("/")[-1].split(".")[0]
        self.posts = lePosts
    
    def loadMeta(self):
        """
        Load all our meta data
        """
        self.meta = eval(getDataFromFile(os.path.join(self.blogPath,"meta.conf")))
    
    def __str__(self):
        """
        Return a string containing all the blog data html formatted
        Think of this as the index page
        """
        blogTitle = '<a href="/"><h1>' + self.meta["title"] + "</h1></a>"
        formattedPosts = [str(p) for p in self.posts]
        print formattedPosts
        return blogTitle + "<br />"  + "<br />".join(formattedPosts)

class server(Daemon):
    """
    Controll all the things
    """
    def __init__(self,blogPath,gitPath):
        blogPath = os.path.join(os.getcwd(),blogPath)
        gitPath = os.path.join(os.getcwd(),gitPath)
        Daemon.__init__(self,os.path.join(blogPath,"gibsy.pid"))
        self.blogPath = blogPath
        self.gitPath = gitPath
        self.blogData = blog(blogPath)
    
    def run(self):
        """
        Start the web server
        """
        self.reload()
        evwsgi.start('0.0.0.0','8080')
        evwsgi.set_base_module(base)
        self.loadWebPaths()
        evwsgi.set_debug(1)
        evwsgi.run()
        runCommand("rm %s" % os.path.join(self.blogPath,"gibsy.pid"))
    def reload(self):
        """
        Reload everything from the file system
        """
        self.blogData.pullFromGit()
        self.blogData.loadPosts()
        self.blogData.loadMeta()
    
    def loadWebPaths(self):
        """
        Load all the blog pages
        """
        for _post in self.blogData.posts:
            evwsgi.wsgi_cb(("/%s" % _post.filename,_post.wsgiCallback))
            print "Linked to /%s to %s" % (_post.filename,str(_post))
        evwsgi.wsgi_cb(("/rss",self.rss))
        evwsgi.wsgi_cb(("",self.index))
    def index(self,eviron,start_response):
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [str(self.blogData)]
    def rss(self,eviron,start_response):
        return [self.blogData.generateRSSXML()]
if __name__ == "__main__":
    command = sys.argv[1]
    if command == "install":
        install()
    if command == "stop":
        serv = server(sys.argv[2],sys.argv[3])
        serv.stop()
    if command == "start": #blog path, git path
        serv = server(sys.argv[2],sys.argv[3])
        serv.start()
    if command == "derp":
        serv = server(sys.argv[2],sys.argv[3])
        serv.run()
        


