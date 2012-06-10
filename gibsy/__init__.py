from gevent import monkey
monkey.patch_all()
from gevent.pywsgi import WSGIServer
import os
import json
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



class geventWSGI(object):
    def __init__(self, addr, port):
        self.port = int(port)
        self.addr = addr
        self.callbacks = {}

    def __getitem__(self, key):
        try:
            return self.callbacks[key]
        except Exception:
            def _404(env, sr):
                sr('404 Not Found', [('Content-Type', 'text/html')])
                return ['<h1> Not Found </h1>']
            return _404

    def __setitem__(self, key, value):
        self.callbacks[key] = value

    def handle(self, env, start_response):
        return self[env['PATH_INFO']](env, start_response)

    def start(self):
        WSGIServer((self.addr, self.port), self.handle).serve_forever()

class Server(Daemon):

    def __init__(self, config_path):
        self.config_path = config_path
        self.config = json.loads(open(self.config_path).read())
        self.gevent_server = geventWSGI(self.config['host'], self.config['port'])
        Daemon.__init__(self, self.config['pid_path'])

    def loadWebPath(self):
        for post in self.blog.posts:
            self.gevent_server["/{0}".format(post.getWebPath())] = post.getPostPage
        self.gevent_server["/rss"] = self.blog.getRSSFeed
        self.gevent_server["/css"] = self.blog.getPygments
        self.gevent_server["/"] = self.blog.getIndexPage

    def update(self):
        current_dir = os.getcwd()
        os.chdir(self.config['git_clone'])
        util.run_command("git pull origin master")
        os.chdir(current_dir)

    def run(self):
        from blog import Blog
        self.update()
        self.blog = Blog(self.config)
        self.loadWebPath()
        self.gevent_server.start()

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
