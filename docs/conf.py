# -*- coding: utf-8 -*-

import os
import sys


# -- General configuration -----------------------------------------------------

_projectpath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

sys.path.insert(0, _projectpath)

from schematics import __version__

on_rtd = bool(os.environ.get('READTHEDOCS')) # Building on Read the Docs?

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.doctest', 'sphinx_navtree']

navtree_shift = True

doctest_path = [_projectpath]
doctest_test_doctest_blocks = 'default'

source_suffix = '.rst'
source_encoding = 'utf-8'

master_doc = 'toc'

exclude_patterns = ['_build']
templates_path = ['_templates']

project = 'Schematics'
copyright = u'2013–2016 Schematics Authors and Contributors'
author = 'Schematics Authors'

_basename = 'schematics'
_title = 'Schematics Documentation'
_subtitle = 'Python Data Structures for Humans'
_project_url = 'https://github.com/schematics/schematics'
_doc_url = 'https://schematics.readthedocs.org'

version = __version__
release = __version__

language = 'en'

today = ''
today_fmt = '%B %d, %Y'

default_role = None
add_function_parentheses = True
add_module_names = False

pygments_style = 'sphinx'

modindex_common_prefix = []


# -- Options for HTML output ---------------------------------------------------

if not on_rtd:
    html_theme = 'sphinx_rtd_theme'

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#html_theme_options = {}

# Add any paths that contain custom themes here, relative to this directory.
#html_theme_path = ['_themes']

# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
#html_title = None

# A shorter title for the navigation bar.  Default is the same as html_title.
#html_short_title = None

html_context = {'master_doc': 'index'}

# The name of an image file (relative to this directory) to place at the top
# of the sidebar.
#html_logo = None

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
#html_favicon = None

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
#html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
#html_use_smartypants = True

# Custom sidebar templates, maps document names to template names.
#html_sidebars = {}

# Additional templates that should be rendered to pages, maps page names to
# template names.
#html_additional_pages = {}

# If false, no module index is generated.
html_domain_indices = False

# If false, no index is generated.
html_use_index = False

# If true, the index is split into individual pages for each letter.
#html_split_index = False

# If true, links to the reST sources are added to the pages.
#html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
#html_show_sphinx = True

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
#html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
#html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
#html_file_suffix = None

# Output file base name for HTML help builder.
htmlhelp_basename = 'Schematicsdoc'


# -- Options for EPUB output ----------------------------------------------

epub_author = author
epub_publisher = author
epub_identifier = _project_url
epub_scheme = 'URL'
epub_uid = 'pub-uid'

epub_show_urls = 'footnote'


# -- Options for LaTeX output --------------------------------------------------

latex_elements = {
    # 'papersize': 'letterpaper',
    # 'pointsize': '10pt',
    # 'preamble': '',
}

# (source start file, target name, title, author, documentclass, toctree_only)
latex_documents = [
    (master_doc, _basename + '.tex', _title, author, 'manual', False),
]

# For "manual" documents, if this is true, then toplevel headings are parts,
# not chapters.
latex_use_parts = True

latex_show_pagerefs = False
latex_domain_indices = False
latex_show_urls = 'footnote'


# -- Options for manual page output --------------------------------------------

# (source start file, name, description, authors, manual section)
man_pages = [
    (master_doc, _basename, _subtitle, author, 1)
]

man_show_urls = False


# -- Options for Texinfo output ------------------------------------------------

# (source start file, target name, title, author, dir menu entry, description, category)
texinfo_documents = [
    (master_doc, _basename, _title, author, project, _subtitle, 'Miscellaneous'),
]

texinfo_domain_indices = False
texinfo_show_urls = 'footnote'


# -- Customization --------------------------------------------------------

def setup(app):
    app.add_stylesheet('https://static.goodtimes.fi/css/bintoro_rtd.css')

