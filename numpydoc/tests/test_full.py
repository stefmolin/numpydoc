from distutils.version import LooseVersion
import os.path as op
import re
import shutil

import pytest
import sphinx
from sphinx.application import Sphinx
from sphinx.util.docutils import docutils_namespace


# Test framework adapted from sphinx-gallery (BSD 3-clause)
@pytest.fixture(scope='module')
def sphinx_app(tmpdir_factory):
    temp_dir = (tmpdir_factory.getbasetemp() / 'root').strpath
    src_dir = op.join(op.dirname(__file__), 'tinybuild')

    def ignore(src, names):
        return ('_build', 'generated')

    shutil.copytree(src_dir, temp_dir, ignore=ignore)
    # For testing iteration, you can get similar behavior just doing `make`
    # inside the tinybuild directory
    src_dir = temp_dir
    conf_dir = temp_dir
    out_dir = op.join(temp_dir, '_build', 'html')
    toctrees_dir = op.join(temp_dir, '_build', 'toctrees')
    # Avoid warnings about re-registration, see:
    # https://github.com/sphinx-doc/sphinx/issues/5038
    kwargs = dict()
    if LooseVersion(sphinx.__version__) >= LooseVersion('1.8'):
        kwargs.update(warningiserror=True, keep_going=True)
    with docutils_namespace():
        app = Sphinx(src_dir, conf_dir, out_dir, toctrees_dir,
                     buildername='html', **kwargs)
        # need to build within the context manager
        # for automodule and backrefs to work
        app.build(False, [])
    return app


def test_MyClass(sphinx_app):
    """Test that class documentation is reasonable."""
    src_dir, out_dir = sphinx_app.srcdir, sphinx_app.outdir
    class_rst = op.join(src_dir, 'generated',
                        'numpydoc_test_module.MyClass.rst')
    with open(class_rst, 'r') as fid:
        rst = fid.read()
    assert r'numpydoc\_test\_module' in rst  # properly escaped
    class_html = op.join(out_dir, 'generated',
                         'numpydoc_test_module.MyClass.html')
    with open(class_html, 'r') as fid:
        html = fid.read()
    # ensure that no autodoc weirdness ($) occurs
    assert '$self' not in html
    assert '/,' not in html
    assert '__init__' in html  # inherited
    # escaped * chars should no longer be preceded by \'s,
    # if we see a \* in the output we know it's incorrect:
    assert r'\*' not in html
    # "self" should not be in the parameter list for the class:
    assert 'self,' not in html
    # check xref was embedded properly (dict should link using xref):
    assert 'stdtypes.html#dict' in html


def test_my_function(sphinx_app):
    """Test that function documentation is reasonable."""
    out_dir = sphinx_app.outdir
    function_html = op.join(out_dir, 'generated',
                            'numpydoc_test_module.my_function.html')
    with open(function_html, 'r') as fid:
        html = fid.read()
    assert r'\*args' not in html
    assert '*args' in html
    # check xref (iterable should link using xref):
    assert 'glossary.html#term-iterable' in html


def test_reference(sphinx_app):
    """Test for bad references"""
    out_dir = sphinx_app.outdir
    html_files = [
        ["index.html"],
        ["generated", "numpydoc_test_module.my_function.html"],
        ["generated", "numpydoc_test_module.MyClass.html"],
    ]

    expected_lengths = [1, 1, 1]

    for html_file, expected_length in zip(html_files, expected_lengths):
        html_file = op.join(out_dir, *html_file)

        with open(html_file, 'r') as fid:
            html = fid.read()

        reference_list = re.findall(r'<a class="fn-backref" href="\#id\d+">(.*)<\/a>', html)

        assert len(reference_list) == expected_length
        for ref in reference_list:
            assert '-' not in ref  # Bad reference if it contains "-" e.g. R1896e33633d5-1