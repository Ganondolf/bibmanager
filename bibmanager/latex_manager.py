# Copyright (c) 2018 Patricio Cubillos and contributors.
# bibmanager is open-source software under the MIT license (see LICENSE).

import re
import numpy as np

import bib_manager as bm


def no_comments(text):
    r"""
    Remove comments from tex file, partially inspired by this:
    https://stackoverflow.com/questions/2319019

    Parameters
    ----------
    text: String
       Content from a latex file.

    Returns
    -------
    no_comments_text: String
       Input text with removed comments (as defined by latex format).

    Examples
    --------
    >>> text = r'''
    Hello, this is dog.
    % This is a comment line.
    This line ends with a comment. % A comment
    However, this is a percentage \%, not a comment.
    OK, byee.'''
    >>> print(no_comments(text))
    Hello, this is dog.
    This line ends with a comment.
    However, this is a percentage \%, not a comment.
    OK, byee.
    """
    return re.sub(r"[^\\]%.*", "", text)


def citations(text):
    """
    Generator to find citations in a tex text.  Partially inspired 
    by this: https://stackoverflow.com/questions/29976397

    Notes
    -----
    Act recursively in case there are references inside the square
    brackets of the cite call.  Only failing case I can think so far
    is if there are nested square brackets.

    Parameters
    ----------
    text: String
       String where to search for the latex citations.

    Yields
    ------
    citation: String
       The citation key.

    Examples
    --------
    >>> import latex_manager as lm
    >>> # Syntax matches any of these calls:
    >>> tex = r'''
    \citep{AuthorA}.
    \citep[pre]{AuthorB}.
    \citep[pre][post]{AuthorC}.
    \citep [pre] [post] {AuthorD}.
    \citep[{\pre},][post]{AuthorE, AuthorF}.
    \citep[pre][post]{AuthorG} and \citep[pre][post]{AuthorH}.
    \citep{
     AuthorI}.
    \citep
    [][]{AuthorJ}.
    \citep[pre
     ][post] {AuthorK, AuthorL}
    \citep[see also \citealp{AuthorM}][]{AuthorN}'''
    >>> for citation in lm.citations(tex):
    >>>     print(citation, end=" ")
    AuthorA AuthorB AuthorC AuthorD AuthorE AuthorF AuthorG AuthorH AuthorI AuthorJ AuthorK AuthorL AuthorM AuthorN

    >>> # Match all of these cite calls:
    >>> tex = r'''
    \cite{AuthorA}, \nocite{AuthorB}, \defcitealias{AuthorC}.
    \citet{AuthorD}, \citet*{AuthorE}, \Citet{AuthorF}, \Citet*{AuthorG}.
    \citep{AuthorH}, \citep*{AuthorI}, \Citep{AuthorJ}, \Citep*{AuthorK}.
    \citealt{AuthorL},     \citealt*{AuthorM},
    \Citealt{AuthorN},     \Citealt*{AuthorO}.
    \citealp{AuthorP},     \citealp*{AuthorQ},
    \Citealp{AuthorR},     \Citealp*{AuthorS}.
    \citeauthor{AuthorT},  \citeauthor*{AuthorU}.
    \Citeauthor{AuthorV},  \Citeauthor*{AuthorW}.
    \citeyear{AuthorX},    \citeyear*{AuthorY}.
    \citeyearpar{AuthorZ}, \citeyearpar*{AuthorAA}.'''
    >>> for citation in lm.citations(tex):
    >>>     print(citation, end=" ")
    AuthorA AuthorB AuthorC AuthorD AuthorE AuthorF AuthorG AuthorH AuthorI AuthorJ AuthorK AuthorL AuthorM AuthorN AuthorO AuthorP AuthorQ AuthorR AuthorS AuthorT AuthorU AuthorV AuthorW AuthorX AuthorY AuthorZ AuthorAA

    >>> with open("sample.tex") as f:
    >>>     tex = f.read()
    >>> tex = lm.no_comments(tex)
    >>> cites = [citation for citation in lm.citations(tex)]
    >>> for key in np.unique(cites):
    >>>     print(key)
    """
    # This RE pattern matches:
    # - Latex commands: \defcitealias, \nocite, \cite
    # - Natbib commands: \cite + p, t, alp, alt, author, year, yearpar
    #                    (as well as their capitalized and starred versions).
    # - Zero or one square brackets (with everything in between).
    # - Zero or one square brackets (with everything in between).
    # - The content of the curly braces.
    # With zero or more blanks in between each expression.
    p = re.compile(r"\\(?:defcitealias|nocite|cite|"
                   r"(?:[Cc]ite(?:p|alp|t|alt|author|year|yearpar)\*?))"
                   r"[\s]*(\[[^\]]*\])?"
                   r"[\s]*(\[[^\]]*\])?"
                   r"[\s]*{([^}]+)")
    # Parse matches, do recursive call on the brakets content, yield keys:
    for left, right, cites in p.findall(text):
        for cite in citations(left):
            yield cite.strip()
        for cite in citations(right):
            yield cite.strip()
        for cite in cites.split(","):
            yield cite.strip()


def build_bib(texfile, bibfile=None):
    """
    Generate a .bib file from a given tex file.

    Parameters
    ----------
    texfile: String
       Name of an input tex file.
    bibfile: String
       Name of an output bib file.  If None, get bibfile name from
       bibliography call inside the tex file.
    """
    with open(texfile, "r") as f:
        tex = f.read()
    tex = no_comments(tex)

    # Extract bibfile name from texfile:
    if bibfile is None:
        biblio = re.findall(r"\\bibliography{([^}]+)", tex)
        if len(biblio) == 0:
            raise Exception("No '\\bibiliography' call found in tex file.")
        bibfile = biblio[0].strip() + ".bib"

    # Extract citation keys from texfile:
    cites = [citation for citation in citations(tex)]
    tex_keys = np.unique(cites)

    # Collect BibTeX references from keys in database:
    bibs = bm.load()
    db_keys = [bib.key for bib in bibs]

    found = np.in1d(tex_keys, db_keys, assume_unique=True)
    if not np.all(found):
        missing = tex_keys[np.where(np.invert(found))]
        print("References not found:\n{:s}".format("\n".join(missing)))

    bibs = [bibs[db_keys.index(key)] for key in tex_keys[found]]
    bm.export(bibs, bibfile=bibfile)
