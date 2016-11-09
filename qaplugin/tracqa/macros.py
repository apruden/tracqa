# -*- coding: utf-8 -*-
"""
Wiki Macros for the plugin.

(c) 2010
"""

from genshi.builder import tag

from trac.core import TracError
from trac.web.chrome import add_stylesheet, Chrome
from trac.wiki.api import parse_args
from trac.wiki.macros import WikiMacroBase

from model import TestCase
from util import parse_period

class TestCaseListMacro(WikiMacroBase):
    """A macro to display test cases outside (or inside)
    the QA module - most commonly Wiki pages.

    All arguments are optional:
    {{{
    [[BlogList]]
    }}}
    
    Available named arguments:
     * `recent=` - max. number of posts
     * `category=` - a category
     * `author=` - an author
     * `period=` - time period of the format YYYY/MM
     * `heading=` - a heading for the list
     * `format=` - type of display (see below for details)
     * `max_size=` - max. number of characters to render for each post
     * `meta=` - use `=off` to hide date, author and categories (default 'on')

    Example showing some available named arguments:
    {{{
    [[BlogList(recent=5, max_size=250, period=2007/12, author=osimons, format=float, heading=Some Trac Posts)]]
    }}}
    
    The arguments for criteria are 'AND'-based, so the above example will render
    at most 5 posts by 'osimons' in December 2007. 
    """
    
    def expand_macro(self, formatter, name, content):

        # Parse content for arguments
        args_list, args_dict = parse_args(content)
        from_dt, to_dt = parse_period(list(args_dict.get('period', '').split('/')))
        category = args_dict.get('category', '')
        author = args_dict.get('author', '')
        recent = int(args_dict.get('recent', 0))
        format = args_dict.get('format', 'inline').lower()
        heading = args_dict.get('heading', '')
        max_size = int(args_dict.get('max_size', 0))
        show_meta = args_dict.get('meta', '') != 'off' and True or False

        # Get blog posts
        all_posts = TestCase.find(self.env)

        # Trim posts against permissions and count
        post_list = []
        post_instances = []
        if format in ['float', 'full']:
            recent = recent or self.env.config.getint('qa', 'num_items_front')
        recent = recent or len(all_posts)
        count = 0
        for post in all_posts:
            if count == recent:
                break
            bp = TestCase(self.env, post[0])
            if 'QA_VIEW' in formatter.req.perm(bp.resource):
                count += 1
                post_instances.append(bp)
                post_list.append(post)

        # Rendering
        add_stylesheet(formatter.req, 'tracqa/css/qa.css')
        add_stylesheet(formatter.req, 'common/css/code.css')

        if format == 'inline':
            data = {'heading': heading,
                    'posts': post_list,
                    'qa_personal_blog': self.config.getbool(
                                                'qa', 'personal_blog'),
                    'show_meta': show_meta,
                    'execute_blog_macro': True}
            return Chrome(self.env).render_template(formatter.req,
                    'qa_macro_monthlist.html', data=data, fragment=True)

        elif format == 'full':
            return self._render_full_format(formatter, post_list,
                                post_instances, heading, max_size, show_meta)

        elif format == 'float':
            # Essentially a 'full' list - just wrapped inside a new div
            return tag.div(self._render_full_format(formatter, post_list,
                                post_instances, heading, max_size, show_meta),
                            class_="blogflash")

        else:
            raise TracError("Invalid 'format' argument used for macro %s." % name)

    def _render_full_format(self, formatter, post_list, post_instances, heading,
                                    max_size, show_meta):
        """ Renters full blog posts. """
        out = tag.div(class_="qa")
        out.append(tag.div(heading, class_="qa-list-title"))
        for post in post_instances:
            data = {'post': post,
                    'qa_personal_blog': self.config.getbool(
                                                'qa', 'personal_blog'),
                    'list_mode': True,
                    'show_meta': show_meta,
                    'execute_blog_macro': True}
            if max_size:
                data['blog_max_size'] = max_size
            out.append(Chrome(self.env).render_template(formatter.req,
                'qa_macro_post.html', data=data, fragment=True))
        return out
