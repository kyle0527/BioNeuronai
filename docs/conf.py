import os
import sys
from datetime import datetime

# -- Path setup --------------------------------------------------------------

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# -- Project information -----------------------------------------------------

project = "BioNeuronAI"
current_year = datetime.utcnow().year
copyright = f"{current_year}, BioNeuronAI"
author = "BioNeuronAI Contributors"

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.autosummary",
    "myst_parser",
]

autosummary_generate = True
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_attr_annotations = True

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}

autodoc_mock_imports = [
    "httpx",
    "aiva_common",
    "aiva_common.enums",
    "aiva_common.schemas",
    "aiva_common.utils",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# -- Myst parser configuration -----------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
