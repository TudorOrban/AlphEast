
import os
import sys


sys.path.insert(0, os.path.abspath("../../src"))


project = "AlphEast"
copyright = "2025, Tudor Andrei Orban"
author = "Tudor Andrei Orban"
release = "0.1.0"

extensions = [
    'sphinx.ext.autodoc', 
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.intersphinx',
    'sphinx_autodoc_typehints'
]

templates_path = ["_templates"]
exclude_patterns = []

html_theme = "furo"
html_static_path = ["_static"]

autodoc_member_order = "bysource"