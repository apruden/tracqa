# -*- coding: utf-8 -*-
"""
TracQa admin panel for some settings related to the plugin.

(c) 2010
"""
#import pdb
#pdb.set_trace()

from pkg_resources import resource_filename

from trac.core import *
from trac.admin import IAdminPanelProvider
from trac.resource import Resource
from trac.web.chrome import add_warning, ITemplateProvider

# Relative imports
from core import QaCore

__all__ = ['QaAdminPanel']

class QaAdminPanel(Component):
    """ Admin panel for settings related to QA plugin. """

    implements(IAdminPanelProvider,ITemplateProvider)

    # IAdminPageProvider
    def get_admin_panels(self, req):
        if 'QA_ADMIN' in req.perm('qa'):
            yield ('qa', 'QA', 'settings', 'Settings')

    def render_admin_panel(self, req, cat, page, path_info):     
        self.log.debug("Hey, varname is %r", req)
        req.perm(Resource('qa', None)).require('QA_ADMIN')

        qa_admin = {}
        qa_core = QaCore(self.env)

        if req.method == "POST":
            if req.args.get('savesettings'):
                self.env.config.set('qa', 'num_items_front',
                    int(req.args.get('numpostsfront')))
                self.env.config.set('qa', 'default_postname',
                    req.args.get('defaultpostname'))
                self.env.config.save()
            elif req.args.get('saveqainfotext'):
                self.env.log.debug("New QA info text = %r" % req.args.get('qainfotext'))
                is_ok = qa_core.set_qainfotext(
                        req.args.get('qainfotext'))
                if is_ok:
                    req.redirect(req.href.admin(req.args['cat_id'],
                            req.args['panel_id']))
                else:
                    add_warning(req, "Error storing text in database. Not saved.")
            else:
                self.log.warning('Unknown POST request: %s', req.args)
        
        qa_admin['qainfotext'] = qa_core.get_qainfotext()
        qa_admin['numpostsfront'] = self.env.config.getint(
                                            'qa', 'num_items_front')
        
        self.log.debug("Hey, varname 1 is %r", req)
        
        return ('qa_admin.html', {'qa_admin': qa_admin})
    
    def get_htdocs_dirs(self):
        """ Makes the 'htdocs' folder inside the egg available. """
        return [('tracqa', resource_filename('tracqa', 'htdocs'))]

    def get_templates_dirs(self):
        """ Location of Trac templates provided by plugin. """
        return [resource_filename('tracqa', 'templates')]
