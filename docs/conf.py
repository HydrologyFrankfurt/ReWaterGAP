# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
# Main ReWaterGAP path
sys.path.insert(0, os.path.abspath('..'))
# Vertical Water Balance path
sys.path.insert(0, os.path.abspath('../model/verticalwaterbalance'))
# Lateral Water Balance path
sys.path.insert(0, os.path.abspath('../model/lateralwaterbalance'))
# Controller path 
sys.path.insert(0, os.path.abspath('../controller'))
# Miscellaneous 
sys.path.insert(0, os.path.abspath('../misc'))



# -- Project information -----------------------------------------------------

project = 'ReWaterGAP'
copyright = '2024, ReWaterGAP'
author = 'ReWaterGAP'


# -- General configuration ---------------------------------------------------
# master_doc = 'index'
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions =  [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'numpydoc',
    'sphinx.ext.mathjax',  
    'sphinx_design',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']


# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'sphinx_rtd_theme'
html_theme = 'pydata_sphinx_theme'
# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#

html_theme_options = {
    "external_links": [],
    "github_url": "https://github.com/HydrologyFrankfurt/ReWaterGAP",
    "twitter_url": "https://twitter.com/HydroFrankfurt",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []

html_logo = "../misc/watergap_logo.png"

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'ReWaterGAP'
