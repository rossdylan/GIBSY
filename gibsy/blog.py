import os
import time
import re
import datetime
import PyRSS2Gen as rss2
import utilities as util

TEMPLATE_HEAD = ""
TEMPLATE_HEAD += '<html>'
TEMPLATE_HEAD += '<link rel="stylesheet" '
TEMPLATE_HEAD += 'href='
TEMPLATE_HEAD += '"http://twitter.github.com'
TEMPLATE_HEAD += '/bootstrap/1.4.0/bootstrap.min.css">'
TEMPLATE_HEAD += '<link href="css" rel="stylesheet" type="text/css">'
TEMPLATE_TAIL = "</html>"

POST_TEMPLATE_HEAD = "<div class='row'><div class='span-two-thirds offset1'>"
POST_TEMPLATE_TAIL = "</div></div>"

class BlogPost(object):

    def __init__(self, path):
        self.post_path = path
        self.body = []

        stats = os.stat(path)
        self.date = time.localtime(stats[8])

        self.title = "Default Title"

        first_line = True
        with open(self.post_path) as f:
            for line in f:
                if first_line:
                    self.title = util.reST_to_html(line)
                    first_line = False
                else:
                    self.body.append(line)
        self.body = util.reST_to_html('\n'.join(self.body))

    def getWebPath(self):
        """
        Get the path for this post
        """

        if "/" in self.post_path:
            return self.post_path.split("/")[-1]
        else:
            return self.post_path

    def getPostTitle(self):
        """
        Return the title for this blog post
        """

        return self.title

    @util.templated(POST_TEMPLATE_HEAD, POST_TEMPLATE_TAIL)
    def getPostBody(self):
        """
        Return the html formatted body of this post
        """

        return self.body

    def getFormattedPost(self):
        """
        Return the fully formatted post in its entirety (including title)
        """

        return ''.join([
            '<a href="{0}">'.format(self.getWebPath()),
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

    @util.wsgify("text/html")
    @util.templated(TEMPLATE_HEAD, TEMPLATE_TAIL)
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

        self.pygments = util.run_command("pygmentize -S colorful -f html")
        self.pygments += "\n pre {line-height: 10px: }"

        post_listing = os.listdir(self.posts_path)
        post_files = [os.path.join(self.posts_path, f) for f in post_listing]
        post_files = util.sort_by_date(post_files)

        for post_file in post_files:
            self.posts.append(BlogPost(post_file))

    @util.wsgify("text/css")
    def getPygments(self):
        return self.pygments

    @util.wsgify("text/html")
    @util.templated(TEMPLATE_HEAD, TEMPLATE_TAIL)
    def getIndexPage(self):
        index = [
            "<title>" + self.blog_title + "</title>",
            '<a href="/"><h1>' + self.blog_title + "</h1></a>",
            "<br />",
            "<body><div class='row'> <div class='span11 offset1'>",
            "<br /><br />".join([post.getFormattedPost() for post in self.posts]),
            "</div></div><body>"
        ]
        return str("\n".join(index))

    @util.wsgify("application/xml")
    def getRSSFeed(self):
        rss = rss2.RSS2(
            title=self.blog_title,
            link=self.config['blog_url'] + "/rss",
            description=self.config['blog_desc'],
            lastBuildDate=datetime.datetime.utcnow(),
            items=[p.getRSSItem(self.config['blog_url']) for p in self.posts])
        return rss.to_xml()
