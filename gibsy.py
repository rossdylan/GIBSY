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
import json


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


def getDataFromFile(filename):
	"""
	Abstract that reading away
	"""
	f = open(filename)
	data = f.read()
	f.close()
	return data


def commitDirectoryStructure(blogPath, gitPath):
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

def createGitHookScript(gitDir, blogDir):
	"""
	Create the git hook needed to update and 
	restart the server when a change is pushed
	to the git repository.
	"""
	parentDir = os.path.join(blogDir, "../")
	script = "#!/bin/bash\ncd %s\npython2.7 gibsy.py stop %s %s\nGIT_DIR=%s\ngit pull\npython2.7 gibsy.py start %s %s" % (parentDir, blogDir, gitDir, gitDir, blogDir, gitDir)
	touch(os.path.join(gitDir, "hooks/post-receive"))
	runCommand("chmod +x %s" % os.path.join(gitDir, "hooks/post-receive"))
	f = open(os.path.join(gitDir, "hooks/post-receive"), 'w')
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
	blogDir = os.path.join(os.getcwd(), blogname)
	postsDir = os.path.join(blogDir, "posts")
	gitDir = os.path.join(os.getcwd(), "%s.git" % blogname)

	#Create all the things
	print "Create Directory Structure"
	os.mkdir(blogDir)
	os.mkdir(postsDir)
	touch(os.path.join(blogDir, "meta.conf"))

	"""we need an example meta.conf because
	if the author forgets what to put in it
	all users are screwed
	"""

	f = open(os.path.join(blogDir, "meta.conf"),'w')
	f.write('{"title":"Example Blog","blogurl":"http://blog.example.com","blogdesc":"Super awesome special blog of win"}')
	f.close()

	touch(os.path.join(postsDir, "first.post"))
	print "Generating Git Repository"
	generateGitRepo(gitDir)

	#Commit/push all the things
	print "Commiting Directory structure to git"
	commitDirectoryStructure(blogDir, gitDir)
	createGitHookScript(gitDir, blogDir)

def generateGitRepo(gitPath):
	"""
	Create a new git repository
	"""
	prevPath = os.getcwd()
	os.mkdir(gitPath)
	os.chdir(gitPath)
	runCommand("git init --bare")
	os.chdir(prevPath)


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


class post(object):
	"""
	Hold all that post-y goodness, class holds single posts
	"""
	def __init__(self, title, body, filename, date):
		"""
		Initialize a post
		"""
		self.filename = filename
		self.title = title
		self.body = body
		self.date = time.localtime(date)

	def wsgiCallback(self, environ, start_response):
		"""
		A method that returns a modified version of the __str__ function
		It is used so people can directly go to a posts page and view its contents
		"""
		start_response('200 OK', [('Content-Type', 'text/html')])
		body = "<br />".join(self.body.split("\n"))
		return ['<link rel="stylesheet" href="http://twitter.github.com/bootstrap/1.4.0/bootstrap.min.css">',
				"<h1>" + self.title + "</h1><br />",
				"<body><div class='row'>",
				"<div class='span8 offset2'>",
				"<div class='hero-unit'>",
				"<p>" + body + "</p>",
				"</div></div></div></body>"]

	def getRSSItem(self, url):
		"""
		Return a PyRSS2Gen.RSSItem containing the posts information
		"""
		return PyRSS2Gen.RSSItem(
				title=self.title,
				link=url + "/" + self.filename,
				description=' '.join([w for w in self.body.split(" ")[0:int(len(self.body)/4)]]),
				guid = PyRSS2Gen.Guid(url + "/" + self.filename),
				pubDate= datetime.datetime(*self.date[0:6]))

	def __str__(self):
		"""
		Return a html formmated string representation of a post
		"""
		body = "<br />".join(self.body.split("\n"))
		return '<h2><a href="/%s">' % self.filename + self.title + "</a></h2><br /><div class='row'><div class='span-two-thirds offset1'><p>" + body + "</p></div></div>"


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
		"""
		Generate the rss feed for a blog
		It contains all the posts
		"""
		rss = PyRSS2Gen.RSS2(title=self.meta['title'] + " Feed",
				link=self.meta['blogurl'] + "/rss",
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
		runCommand("git pull origin master")
		os.chdir(currentDir)

	def sortByDate(self, filesList):
		"""
		Sort files in descending order of most recently modified
		"""
		dateList = []
		for file in filesList:
			stats = os.stat(file)
			lastModDate = time.localtime(stats[8])
			dateList.append((lastModDate, file))
		dateList.sort()
		dateList.reverse()
		return [f[1] for f in dateList]

	def loadPosts(self):
		"""
		Load all the posts in the posts directory
		"""
		dirList = os.listdir(self.postsPath)
		postFileList = [os.path.join(self.postsPath, f) for f in dirList if f.endswith(".post")]
		postFileList = self.sortByDate(postFileList)
		lePosts = []
		for postFile in postFileList:
			postData = getDataFromFile(postFile)
			lines = postData.split("\n")
			title = lines[0]
			lines = lines[1:]
			date = os.stat(postFile)[8]
			modifiedLines = []
			for line in lines:
				words = line.split(" ")
				modifiedWords = []
				for word in words:
					if word.startswith("http://") or word.startswith("https://"):
						modifiedWords.append("<a href>" + word + "</a>")
					else:
						modifiedWords.append(word)
				modifiedLines.append(' '.join(modifiedWords))
			body = '\n'.join(modifiedLines)
			lePosts.append(post(title, body, postFile.split("/")[-1].split(".")[0], date))
			print "loaded post %s" % postFile.split("/")[-1].split(".")[0]
		self.posts = lePosts

	def loadMeta(self):
		"""
		Load all our meta data
		"""
		self.meta = json.loads(getDataFromFile(os.path.join(self.blogPath, "meta.conf")))
		print self.meta

	def __str__(self):
		"""
		Return a string containing all the blog data html formatted
		Think of this as the index page
		"""
		blogTitle = '<a href="/"><h1>' + self.meta["title"] + "</h1></a>"
		formattedPosts = [str(p) for p in self.posts]
		print formattedPosts
		return blogTitle + "<br />"  + "<body><div class='row'><div class='span11 offset1'>" + "<br />".join(formattedPosts) + "</div></div></body>"


class server(Daemon):
	"""
	Controll all the things
	"""
	def __init__(self,blogPath,gitPath):
		blogPath = os.path.join(os.getcwd(), blogPath)
		gitPath = os.path.join(os.getcwd(), gitPath)
		Daemon.__init__(self,os.path.join(blogPath, "gibsy.pid"))
		self.blogPath = blogPath
		self.gitPath = gitPath
		self.blogData = blog(blogPath)

	def run(self):
		"""
		Start the web server
		"""
		self.reload()
		evwsgi.start('0.0.0.0', '31338')
		evwsgi.set_base_module(base)
		self.loadWebPaths()
		evwsgi.set_debug(1)
		evwsgi.run()
		runCommand("rm %s" % os.path.join(self.blogPath, "gibsy.pid"))

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
			evwsgi.wsgi_cb(("/%s" % _post.filename, _post.wsgiCallback))
			print "Linked to /%s to %s" % (_post.filename, str(_post))
		evwsgi.wsgi_cb(("/rss", self.rss))
		evwsgi.wsgi_cb(("", self.index))

	def index(self,eviron,start_response):
		"""
		Return the html representation of the blogs index page
		"""
		start_response('200 OK', [('Content-Type', 'text/html')])
		return ['<link rel="stylesheet" href="http://twitter.github.com/bootstrap/1.4.0/bootstrap.min.css">',
				str(self.blogData)]

	def rss(self,eviron,start_response):
		"""
		return a valid rss feed for the blog
		"""
		return [self.blogData.generateRSSXML()]


"""
Time to create a simple command line interface,
it kinda acts like a bastardized init script
"""


if __name__ == "__main__":
	command = sys.argv[1]

	if command == "install":
		install()

	if command == "stop":
		print "Stopping Server"
		serv = server(sys.argv[2], sys.argv[3])
		serv.stop()

	if command == "start": #blog path, git path
		serv = server(sys.argv[2], sys.argv[3])
		print "Server starting..."
		serv.start()

	if command == "restart":
		serv = server(sys.argv[2],sys.argv[3])
		print "Server Stopping..."
		serv.stop()
		print "Server Starting..."
		serv.start()

	if command == "debug":
		print "Starting Server in Debug mode"
		serv = server(sys.argv[2], sys.argv[3])
		serv.run()
