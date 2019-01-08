# Copyright (c) 2018-2019 Patricio Cubillos and contributors.
# bibmanager is open-source software under the MIT license (see LICENSE).

import sys
import os
import argparse
import textwrap
import prompt_toolkit

sys.path.append(os.path.dirname(os.path.realpath(__file__)))
import bibmanager as bm
# FINDME: Temporary hack until setting BM as a package:
import latex_manager  as lm
import config_manager as cm
import ads_manager    as am
from utils import BOLD, END


def cli_init(args):
    """Command-line interface for init call."""
    if args.bibfile is not None and not os.path.exists(args.bibfile):
        raise FileNotFoundError("Input BibTeX file '{:s}' does not exist.".
                        format(args.bibfile))
    if args.bibfile is not None:
        bibzero = " with BibTeX file: '{:s}'.".format(args.bibfile)
        args.bibfile = os.path.realpath(args.bibfile)
    else:
        bibzero = "."
    print("Initializing new bibmanager database{:s}".format(bibzero))
    bm.init(args.bibfile)


def cli_merge(args):
    """Command-line interface for merge call."""
    if args.bibfile is not None and not os.path.exists(args.bibfile):
        raise FileNotFoundError("Input BibTeX file '{:s}' does not exist.".
                        format(args.bibfile))
    if args.bibfile is not None:
        args.bibfile = os.path.realpath(args.bibfile)
    bm.merge(bibfile=args.bibfile, take=args.take)
    print("\nMerged new BibTeX file '{:s}' into bibmanager database.".
          format(args.bibfile))


def cli_edit(args):
    """Command-line interface for edit call."""
    bm.edit()


def cli_add(args):
    """Command-line interface for add call."""
    bm.add_entries(take=args.take)


def cli_search(args):
    """Command-line interface for search call."""
    year = args.year
    # Cast year string to integer or list of integers:
    if year is None:
        year = None
    elif len(year) == 4 and year.isnumeric():
        year = int(year)
    elif len(year) == 5 and year.startswith('-') and year[1:].isnumeric():
        year = [0, int(year[1:])]
    elif len(year) == 5 and year.endswith('-') and year[0:4].isnumeric():
        year = [int(year[0:4]), 9999]
    elif len(year) == 9 and year[0:4].isnumeric() and year[5:].isnumeric():
        year = [int(year[0:4]), int(year[5:9])]
    else:
        raise ValueError("Invalid input year format: {:s}".format(year))

    matches = bm.search(args.author, year, args.title)

    # Display outputs depending on the verb level:
    if args.verb >= 3:
        bm.display_bibs(labels=None, bibs=matches)
        return

    wrap_kw = {'width':80, 'subsequent_indent':"   "}
    for match in matches:
        title = textwrap.fill("Title: {:s}, {:d}".format(match.title,
            match.year), **wrap_kw)
        authors = textwrap.fill("Authors: {:s}".format(
            match.get_authors(short=args.verb<2)), **wrap_kw)
        keys = "\nkey: {:s}".format(match.key)
        if args.verb > 0 and match.eprint is not None:
            keys = "\narXiv url: http://arxiv.org/abs/{:s}{:s}".format(
                match.eprint, keys)
        if args.verb > 0 and match.adsurl is not None:
            keys = "\nADS url:   {:s}{:s}".format(match.adsurl, keys)
            keys = "\nbibcode:   {:s}{:s}".format(match.bibcode, keys)
        print("\n{:s}\n{:s}{:s}".format(title, authors, keys))


def cli_export(args):
    """Command-line interface for export call."""
    path, bfile = os.path.split(os.path.realpath(args.bibfile))
    if not os.path.exists(path):
        raise FileNotFoundError("Output dir does not exists: '{:s}'".
                                format(path))
    # TBD: Check for file extension
    bm.export(bm.load(), bibfile=args.bibfile)


def cli_config(args):
    """Command-line interface for config call."""
    if args.param is None:
        cm.display()
    elif args.value is None:
        cm.help(args.param)
    else:
        cm.set(args.param, args.value)


def cli_bibtex(args):
    """Command-line interface for bibtex call."""
    lm.build_bib(args.texfile, args.bibfile)


def cli_latex(args):
    """Command-line interface for latex call."""
    lm.compile_latex(args.texfile, args.paper)


def cli_pdflatex(args):
    """Command-line interface for pdflatex call."""
    lm.compile_pdflatex(args.texfile)


def cli_ads_search(args):
    """Command-line interface for ads-search call."""
    am.manager(args.querry)


def cli_ads_add(args):
    """Command-line interface for ads-add call."""
    if args.bibcode is None and args.key is None:
        inputs = prompt_toolkit.prompt(
            "Enter pairs of ADS bibcodes and BibTeX keys, one pair per line\n"
            "separated by blanks (press META+ENTER or ESCAPE ENTER when "
            "done):\n", multiline=True)
        bibcodes, keys = [], []
        inputs = inputs.strip().split('\n')
        for line in inputs:
            if len(line.split()) == 0:
                continue
            elif len(line.split()) != 2:
                print("\nError: Invalid syntax, each line must have two strings"
                      " specifying a bibcode\n and key, separated by a blank.")
                return
            bibcode, key = line.split()
            bibcodes.append(bibcode)
            keys.append(key)

    elif args.bibcode is not None and args.key is not None:
        bibcodes = [args.bibcode]
        keys     = [args.key]
    else:
        print("\nError: Invalid input, 'bibm ads-add' expects either zero or "
              "two arguments.")
        return
    am.add_bibtex(bibcodes, keys)


def cli_ads_update(args):
    """Command-line interface for ads-update call."""
    update_keys = args.update == 'arxiv'
    am.update(update_keys)


def main():
    """
    Bibmanager command-line interface.

    Partially inspired by these:
    - https://stackoverflow.com/questions/7869345/
    - https://stackoverflow.com/questions/32017020/
    """
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('-v', '--version', action='version',
        help="Show bibmanager's version.",
        version='bibmanager version {:s}'.format(bm.__version__))

    # Parser Main Documentation:
    main_description = """
BibTeX Database Management:
---------------------------
  init        Initialize the bibmanager database.
  merge       Merge a BibTeX file into the bibmanager database.
  edit        Edit the bibmanager database in a text editor.
  add         Add entries into the bibmanager database.
  search      Search entries in the bibmanager database.
  export      Export the bibmanager database into a bib file.
  config      Manage the bibmanager configuration parameters.

LaTeX Management:
----------------
  bibtex      Generate a BibTeX file from a LaTeX file.
  latex       Compile a LaTeX file with the latex command.
  pdflatex    Compile a LaTeX file with the pdflatex command.

ADS Management:
---------------
  ads-search  Do a querry on ADS.
  ads-add     Add entries from ADS by bibcode into the bibmanager database.
  ads-update  Update bibmanager database cross-checking entries with ADS.

For additional details on a specific command, see 'bibm command -h'.
See the full bibmanager docs at http://pcubillos.github.io/bibmanager

Copyright (c) 2018-2019 Patricio Cubillos and contributors.
bibmanager is open-source software under the MIT license, see:
https://github.com/pcubillos/bibmanager/blob/master/LICENSE
"""

    # And now the sub-commands:
    sp = parser.add_subparsers(title="These are the bibmanager commands",
        description=main_description, metavar='command')

    # Database Management:
    init_description = """
{:s}Initialize the bibmanager database.{:s}

Description
  This command initializes the bibmanager database (from scratch).
  It creates a .bibmanager/ folder in the user folder (if it does not
  exists already), and it (re)sets the bibmanager configuration to
  its default values.

  If the user provides the 'bibfile' argument, this command will
  populate the database with the entries from that file; otherwise,
  it will set an empty database.

  Note that this will overwrite any pre-existing database.  In
  principle the user should not execute this command more than once
  in a given CPU.""".format(BOLD, END)
    init = sp.add_parser('init', description=init_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    init.add_argument("bibfile", action="store", nargs='?',
        help="Path to an existing BibTeX file.")
    init.set_defaults(func=cli_init)


    merge_description = """
{:s}Merge a BibTeX file into the bibmanager database.{:s}

Description
  This command merges the content from an input BibTeX file with the
  bibmanager database.

  The optional 'take' arguments defines the protocol for possible-
  duplicate entries.  Either take the 'old' entry (database), take
  the 'new' entry (bibfile), or 'ask' the user through the prompt
  (displaying the alternatives).  bibmanager considers four fields
  to check for duplicates: doi, isbn, bibcode, and eprint.

  Additionally, bibmanager considers two more cases (always asking):
  (1) new entry has duplicate key but different content, and
  (2) new entry has duplicate title but different key.
""".format(BOLD, END)
    merge = sp.add_parser('merge', description=merge_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    merge.add_argument("bibfile", action="store",
        help="Path to an existing BibTeX file.")
    merge.add_argument("take", action="store", nargs='?', metavar='take',
        help="Decision protocol for duplicates (choose: {%(choices)s}, "
        "default: %(default)s)", choices=['old','new','ask'], default='old')
    merge.set_defaults(func=cli_merge)


    edit_description = """
{:s}Edit the bibmanager database in a text editor.{:s}

Description
  This command let's you manually edit the bibmanager database,
  in your pre-defined text editor.  Once finished editing, save and
  close the text editor, and press ENTER in the terminal to
  incorporate the edits (edits after continuing on the terminal won't
  count).

  bibmanager selects the OS default text editor.  But the user can
  set a preferred editor, see 'bibm config -h' for more information.
""".format(BOLD, END)
    edit = sp.add_parser('edit', description=edit_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    edit.set_defaults(func=cli_edit)


    add_description = """
{:s}Add entries into the bibmanager database.{:s}

Description
  This command allows the user to manually add BibTeX entries into
  the bibmanager database through the terminal prompt.

  The optional 'take' argument defines the protocol for possible-
  duplicate entries.  Either take the 'old' entry (database), take
  the 'new' entry (bibfile), or 'ask' the user through the prompt
  (displaying the alternatives).  bibmanager considers four fields
  to check for duplicates: doi, isbn, bibcode, and eprint.

  Additionally, bibmanager considers two more cases (always asking):
  (1) new entry has duplicate key but different content, and
  (2) new entry has duplicate title but different key.
""".format(BOLD, END)
    add = sp.add_parser('add', description=add_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    add.add_argument("take", action="store", nargs='?', metavar='take',
        help="Decision protocol for duplicates (choose: {%(choices)s}, "
        "default: %(default)s)", choices=['old','new','ask'], default='new')
    add.set_defaults(func=cli_add)


    search_description = """
{:s}Search entries in the bibmanager database.{:s}

Description
  This command allows the user to search for entries in the bibmanager
  database by authors, years, and keywords in title.  The matching
  results are displayed on screen according to the specified verbosity.
  For search arguments that include a blank space, the user can set
  the string within quotes.

  The user can restrict the search to one or more authors, and can
  request a first-author match by including the '^' character before
  an author name (see examples below).

  The user can restrict the publication year to an specific year,
  to a range of years, or to open-end range of years (see examples
  below).

  Finally, the user can restrict the search to multiple strings in
  the title (see examples below).  Note these are case-insensitive.

  There are four levels of verbosity (see examples below):
  - zero shows the title, year, first author, and key;
  - one adds the ADS and arXiv urls;
  - two adds the full list of authors;
  - and three displays the full BibTeX entry.

Examples
  # Search by last name:
  bibm search -a oliphant
  # Search by last name and initials (note blanks require one to use quotes):
  bibm search -a 'oliphant, t'
  # Search by first-author only:
  bibm search -a '^oliphant, t'
  # Search multiple authors:
  bibm search -a 'oliphant, t' 'jones, e'

  # Seach by author, year, and title words/phrases:
  bibm search -a 'oliphant, t' -y 2006 -t numpy
  # Search multiple words/phrases in title:
  bibm search -t 'HD 209458b' 'atmospheric circulation'

  # Search on specific year:
  bibm search -a 'cubillos, p' -y 2016
  # Search anything between the specified years:
  bibm search -a 'cubillos, p' -y 2014-2016
  # Search anything up to the specified year:
  bibm search -a 'cubillos, p' -y -2016
  # Search anything since the specified year:
  bibm search -a 'cubillos, p' -y 2016-

  # Display title, year, first author, and key:
  bibm search -a 'Burbidge, E'
  # Display title, year, first author, and all keys/urls:
  bibm search -a 'Burbidge, E' -v
  # Display title, year, author list, and all keys/urls:
  bibm search -a 'Burbidge, E' -vv
  # Display full BibTeX entry:
  bibm search -a 'Burbidge, E' -vvv
""".format(BOLD, END)
    search = sp.add_parser('search', description=search_description,
        usage="bibm search [-h] [-v] [-a AUTHOR ...] [-y YEAR] [-t TITLE ...]",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    search.add_argument('-a', '--author', action='store', nargs='+',
        help='Search by author.')
    search.add_argument('-y', '--year', action='store',
        help='Restrict search to a year (e.g., -y 2018) or to a year range '
             '(e.g., -y 2018-2020).')
    search.add_argument('-t', '--title', action='store', nargs='+',
        help='Search by keywords in title.')
    search.add_argument('-v', '--verb', action='count', default=0,
        help='Set output verbosity.')
    search.set_defaults(func=cli_search)


    export_description = """
{:s}Export the bibmanager database into a bib file.{:s}

Description
  Export the entire bibmanager database into a bibliography file to a
  .bib or .bbl format according to the file extension of the
  'bibfile' argument (TBD: for the moment, only export to .bib).
""".format(BOLD, END)
    export = sp.add_parser('export', description=export_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    export.add_argument("bibfile", action="store",
        help="Path to an output BibTeX file.")
    export.set_defaults(func=cli_export)


    config_description = """
{:s}Manage the bibmanager configuration parameters.{:s}

Description
  This command displays or sets the value of bibmanager config parameters.
  There are five parameters that can be set by the user:
  - style       sets the color-syntax style of displayed BibTeX entries.
  - text_editor sets the text editor for 'bibm edit' calls.
  - paper       sets the default paper format for latex compilation.
  - ads_token   sets the token required for ADS requests.
  - ads_display sets the number of entries to show at once for ADS searches.

  The number of arguments determines the action of this command (see
  examples below):
  - with no arguments, display all available parameters and values.
  - with the 'param' argument, display detailed info on the specified
    parameter and its current value.
  - with both 'param' and 'value' arguments, set the value of the parameter.

Examples
  # Display all config parameters and values:
  bibm config
  # Display value and help for the style parameter:
  bibm config style
  # Set the value of the BibTeX color-syntax:
  bibm config style autumn
""".format(BOLD, END)
    config = sp.add_parser('config',  description=config_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    config.add_argument("param", action="store", nargs='?',
        help="A bibmanager config parameter.")
    config.add_argument("value", action="store", nargs='?',
        help="Value for a bibmanager config parameter.")
    config.set_defaults(func=cli_config)


    # Latex Management:
    bibtex_description = """
{:s}Generate a BibTeX file from a LaTeX file.{:s}

Description
  This command generates a BibTeX file by searching for the citation
  keys in the input LaTeX file, and stores the output into BibTeX file,
  named after the argument in the '\\bibliography{{bib_file}}' call in
  the LaTeX file.  Alternatively, the user can specify the name of the
  output BibTeX file with the 'bibfile' argument.

  Any citation key not found in the bibmanager database, will be
  shown on the screen prompt.
""".format(BOLD, END)
    bibtex = sp.add_parser('bibtex', description=bibtex_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    bibtex.add_argument("texfile", action="store",
        help="Path to an existing LaTeX file.")
    bibtex.add_argument("bibfile", action="store", nargs='?',
        help="Path to an output BibTeX file.")
    bibtex.set_defaults(func=cli_bibtex)


    latex_description="""
{:s}Compile a LaTeX file using the latex command.{:s}

Description
  This command compiles a LaTeX file using the latex command,
  executing the following calls:
  - Compute a BibTex file out of the citation calls in the LaTeX file.
  - Remove all outputs from previous compilations.
  - Call latex, bibtex, latex, latex to produce a .dvi file.
  - Call dvi2ps and ps2pdf to produce the final .pdf file.

  Prefer this command over the 'bibm pdflatex' command when the LaTeX
  file contains .ps or .eps figures (as opposed to .pdf, .png, or .jpeg).

  Note that the user does not necessarily need to be in the dir
  where the LaTeX files are.
""".format(BOLD, END)
    latex = sp.add_parser('latex', description=latex_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    latex.add_argument("texfile", action="store",
        help="Path to an existing LaTeX file.")
    latex.add_argument("paper", action="store", nargs='?',
        help="Paper format, e.g., letter or A4 (default=%(default)s).",
        default=cm.get('paper'))
    latex.set_defaults(func=cli_latex)


    pdflatex_description = """
{:s}Compile a LaTeX file using the pdflatex command.{:s}

Description
  This command compiles a LaTeX file using the pdflatex command,
  executing the following calls:
  - Compute a BibTeX file out of the citation calls in the LaTeX file.
  - Remove all outputs from previous compilations.
  - Call pdflatex, bibtex, pdflatex, pdflatex to produce a .pdf file.

  Prefer this command over the 'bibm latex' command when the LaTeX file
  contains .pdf, .png, or .jpeg figures (as opposed to .ps or .eps).

  Note that the user does not necessarily need to be in the dir
  where the LaTeX files are.
""".format(BOLD, END)
    pdflatex = sp.add_parser('pdflatex', description=pdflatex_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    pdflatex.add_argument("texfile", action="store",
        help="Path to an existing LaTeX file.")
    pdflatex.set_defaults(func=cli_pdflatex)


    # ADS Management:
    asearch_description = f"""
{BOLD}Do a querry on ADS.{END}

Description
  This command enables ADS querries.  The querry syntax is identical to
  any querry in the new ADS's one-box search engine:
  https://ui.adsabs.harvard.edu.
  Here there is a detailed documentations for ADS searches:
  https://adsabs.github.io/help/search/search-syntax
  See below for typical querry examples.

  A querry will display at most 'ads_display' entries on screen at once
  (see 'bibm config ads_display').  If a querry matched more entries,
  the user can execute the 'bibm ads-search' command without arguments
  to display the next set of entries.

  Note that:
  (1) The entire querry argument must be set within single quotes.
  (2) ADS-field values that use quotes, must use double quotes.

Examples
  # Search entries for author (display first set of entries, newest to oldest):
  bibm ads-search 'author:"^Fortney, J"'
  # Display the next set of entries that matched this querry:
  bibm ads-search

  # Search by author in article:
  bibm ads-search 'author:"Fortney, J"'
  # Search by first author:
  bibm ads-search 'author:"^Fortney, J"'
  # Search multiple authors:
  bibm ads-search 'author:("Fortney, J" AND "Showman, A")'

  # Seach by author AND year:
  bibm ads-search 'author:"Fortney, J" year:2010'
  # Seach by author AND year range:
  bibm ads-search 'author:"Fortney, J" year:2010-2019'
  # Search by author AND words/phrases in title:
  bibm ads-search 'author:"Fortney, J" title:Spitzer'
  # Search by author AND words/phrases in abstract:
  bibm ads-search 'author:"Fortney, J" abs:Spitzer'

  # Search by author AND request only articles:
  bibm ads-search 'author:"Fortney, J" property:article'
  # Search by author AND request only peer-reviewed articles:
  bibm ads-search 'author:"Fortney, J" property:refereed'
"""
    asearch = sp.add_parser('ads-search', description=asearch_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    asearch.add_argument('querry', action='store', default=None, nargs='?',
        help='ADS querry input.')
    asearch.set_defaults(func=cli_ads_search)


    ads_add_description = f"""
{BOLD}Add entries from ADS by bibcode into the bibmanager database.{END}

Description
  This command add BibTeX entries from ADS by specifying pairs of
  ADS bibcodes and BibTeX keys.

  Executing this command without arguments (i.e., 'bibm ads-add') launches
  an interactive prompt session allowing the user to enter multiple
  bibcode, key pairs.

  By default, added entries replace previously existent entries in the
  bibmanager database.

Examples
  # Let's search and add the greatest astronomy PhD thesis of all times:
  bibm ads-search 'author:"^payne, cecilia" doctype:phdthesis'

  Title: Stellar Atmospheres; a Contribution to the Observational Study of
      High Temperature in the Reversing Layers of Stars.
  Authors: Payne, Cecilia Helena
  adsurl: https://ui.adsabs.harvard.edu/\#abs/1925PhDT.........1P
  bibcode: 1925PhDT.........1P

  # Add the entry to the bibmanager database:
  bibm ads-add 1925PhDT.........1P Payne1925phdStellarAtmospheres

"""
    ads_add = sp.add_parser('ads-add', description=ads_add_description,
        usage="bibm ads-add [-h] [bibcode key]",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ads_add.add_argument('bibcode', action='store', nargs='?',
        help='The ADS bibcode of an entry.')
    ads_add.add_argument('key', action='store', nargs='?',
        help='BibTeX key to assign to the entry.')
    ads_add.set_defaults(func=cli_ads_add)


    ads_update_description = f"""
{BOLD}Update bibmanager database cross-checking entries with ADS.{END}

Description
  This command triggers an ADS search of all entries in the bibmanager
  database that have a 'bibcode' field.  Replacing these entries with
  the output from ADS.

  The main utility of this command is to auto-update entries that
  were added as arXiv version, with their published version.

  For arXiv updates, this command updates automatically the year and
  journal of the key (where possible).  This is done by searching for
  the year and the string 'arxiv' in the key, using the bibcode info.

  For example, an entry with key 'NameEtal2010arxivGJ436b' whose bibcode
  changed from '2010arXiv1007.0324B' to '2011ApJ...731...16B', will have
  a new key 'NameEtal2011apjGJ436b'.
  To disable this feature, set the 'update_keys' optional argument to no.
"""
    ads_update = sp.add_parser('ads-update', description=ads_update_description,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ads_update.add_argument('update', action='store', metavar='update_keys',
        default='arxiv', nargs='?', choices=['no', 'arxiv'],
        #default='arxiv', nargs='?', choices=['no', 'arxiv', 'all'],
        help='Update the keys of the entries. (choose from: {%(choices)s}, '
             'default: %(default)s).')
    ads_update.set_defaults(func=cli_ads_update)

    # Parse command-line args:
    args, unknown = parser.parse_known_args()
    # Make bibmanager calls:
    args.func(args)


if __name__ == "__main__":
    main()