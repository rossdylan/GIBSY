#GIBSY#
	GIt Blogging SYstem
	GIBSY is a extremely lightweight blogging system designed to work with a git
	repository.

##Dependancies:#
	-python2.7
		-FAPWS3
			-libev
		-PyRSS2Gen
	-git

##Commands:#
	### install #:
		Installs GIBSY to the current directory. This means it generates 2
		directories based in the current path. The first directory is the blog
		directory <blogname>/ the second directory is the git repo
		<blogname>.git/ Also during this process a basic blog with a minimal
		meta.conf and first.post are pushed to the git repo. The final step of
		the install process is to generate a git hook that restarts the server
		to recieve updates whenever the git repo is pushed to.

	### start:#
		start <blogPath> <gitPath>
		Start the web server and begin hosting the blog.
		the FAPWS3 web server is pretty fast and since all blog posts are just
		text and are loaded into memory the website loads really quickly (or at
		least it did in my simple tests, feel free to prove me wrong).

	### stop:#
		stop <blogPath> <gitPath>
		Exactly as the name entails, only now that gibsy goes into daemon mode
		it hunts down the pid and KILLS IT.

	### restart:#
		restart <blogPath> <gitPath>
			Equivalent to gibsy stop && gibsy start

	### debug:#
		debug <blogPath> <gitPath>
		Runs gibsy in the foreground So problems can be diagnosed.

##Extending GIBSY:#
	The code as of 12/4/11 is kinda messy but it will improve as time goes on.
	Most of initial code was written in a 2 day personal hackathon so it is of
	course a bit messy and unorganized, anyway...

	The code comes in several parts:
	
		###Install functions:#
			All of these functions are used during the install process to set
			everything up. These are all located at the begining of gibsy.py,
			There is a comment in the code splitting the install functions and
			the other stuff

		###Post and Blog classes:#
			These classes are filled with things to make dealing with the
			blog's data a bit easier. There are definately some inefficencies
			in this code...

		###Server class:#
			the server class puts everything together. It handles reloading the
			blog, accepting signals, catching exceptions, loading the web
			paths, etc.
		
		###Command section:#
			Commands and stuff go here, just the basic logic for accepting
			input and deciding what command function to use.
