from __future__ import annotations

import os
import re
import sys
import textwrap
from argparse import ArgumentParser, PARSER
from itertools import islice
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from rich.containers import Lines
from rich.text import Text
from rich_argparse import RichHelpFormatter

from onyo import commands
from onyo.lib.ui import ui

if TYPE_CHECKING:
    from argparse import Action
    from collections.abc import Iterator


class WrappedTextRichHelpFormatter(RichHelpFormatter):
    def _rich_format_action(self, action: Action) -> Iterator[tuple[Text, Text | None]]:
        parts = super()._rich_format_action(action)
        # remove the superfluous first line (<COMMANDS>) of the subcommands section
        if action.nargs == PARSER:
            parts = islice(parts, 1, None)

        return parts

    def _rich_split_lines(self, text: Text, width: int) -> Lines:
        lines = Lines()
        for line in text.split():
            lines.extend(line.wrap(self.console, width))
        return lines

    def _rich_fill_text(self, text: Text, width: int, indent: Text) -> Text:
        lines = self._rich_split_lines(text, width)
        return Text("\n").join(indent + line for line in lines) + "\n"

    def _rich_format_text(self, text: str) -> Text:
        text = prepare_rst_for_rich(text)

        return super()._rich_format_text(text)


def prepare_rst_for_rich(text: str) -> str:
    """
    This is a very naive approach to cleanup docstrings and help text in
    preparation to print to the terminal.

    Some effort is made to stylize RST markup.
    """
    # de-indent text
    text = textwrap.dedent(text).strip()

    # stylize arg descriptors (ALL CAPS ARGS)
    text = re.sub('\*\*([A-Z\-]+)\*\*', r'[dark_cyan]\1[/dark_cyan]', text)

    # stylize ** (bold)
    text = re.sub('\*\*([^*]+)\*\*', r'[bold]\1[/bold]', text)

    # stylize ``` (code blocks)
    text = re.sub('```([^`]+)```', r'[underline]\1[/underline]', text)

    # strip `` (inline code markers) for flags
    # flags are auto-colorized by rich-argparse
    text = re.sub('``(-[^`]+)``', r'\1', text)

    # stylize remaining `` (inline code markers)
    text = re.sub('``([^`]+)``', r'[bold magenta]\1[/bold magenta]', text)

    # make bullet points prettier
    text = text.replace(' * ', ' • ')

    # remove escaping
    text = text.replace('\\', '')

    return text


def build_parser(parser, args: dict) -> None:
    """
    Add arguments to a parser.
    """
    for cmd in args:
        args[cmd]['dest'] = cmd
        try:
            parser.add_argument(
                *args[cmd]['args'],
                **{k: v for k, v in args[cmd].items() if k != 'args'} | {'help': prepare_rst_for_rich(args[cmd]['help'])})
        except KeyError:
            parser.add_argument(**{k: v for k, v in args[cmd].items()} | {'help': prepare_rst_for_rich(args[cmd]['help'])})


subcmds = None


def setup_parser() -> ArgumentParser:
    from onyo.onyo_arguments import args_onyo
    from onyo.commands.cat import args_cat
    from onyo.commands.config import args_config
    from onyo.commands.edit import args_edit
    from onyo.commands.get import args_get
    from onyo.commands.history import args_history
    from onyo.commands.init import args_init
    from onyo.commands.mkdir import args_mkdir
    from onyo.commands.mv import args_mv
    from onyo.commands.new import args_new
    from onyo.commands.rm import args_rm
    from onyo.commands.set import args_set
    from onyo.commands.shell_completion import args_shell_completion
    from onyo.commands.tree import args_tree
    from onyo.commands.unset import args_unset

    global subcmds

    parser = ArgumentParser(
        description='A text-based inventory system backed by git.',
        formatter_class=WrappedTextRichHelpFormatter
    )
    build_parser(parser, args_onyo)

    # subcommands
    subcmds = parser.add_subparsers(
        title='commands',
        dest='cmd'
    )
    subcmds.metavar = '<command>'
    #
    # subcommand "cat"
    #
    cmd_cat = subcmds.add_parser(
        'cat',
        description=commands.cat.__doc__,
        formatter_class=parser.formatter_class,
        help='Print the contents of assets to the terminal.'
    )
    cmd_cat.set_defaults(run=commands.cat)
    build_parser(cmd_cat, args_cat)
    #
    # subcommand "config"
    #
    cmd_config = subcmds.add_parser(
        'config',
        description=commands.config.__doc__,
        formatter_class=parser.formatter_class,
        help='Set, query, and unset Onyo repository configuration options.'
    )
    cmd_config.set_defaults(run=commands.config)
    build_parser(cmd_config, args_config)
    #
    # subcommand "edit"
    #
    cmd_edit = subcmds.add_parser(
        'edit',
        description=commands.edit.__doc__,
        formatter_class=parser.formatter_class,
        help='Open assets using an editor.'
    )
    cmd_edit.set_defaults(run=commands.edit)
    build_parser(cmd_edit, args_edit)
    #
    # subcommand "fsck"
    #
    cmd_fsck = subcmds.add_parser(
        'fsck',
        description=commands.fsck.__doc__,
        formatter_class=parser.formatter_class,
        help='Run a suite of integrity checks on the Onyo repository and its contents.'
    )
    cmd_fsck.set_defaults(run=commands.fsck)
    #
    # subcommand "get"
    #
    cmd_get = subcmds.add_parser(
        'get',
        description=commands.get.__doc__,
        formatter_class=parser.formatter_class,
        help='Return and sort asset values matching query patterns.'
    )
    cmd_get.set_defaults(run=commands.get)
    build_parser(cmd_get, args_get)
    #
    # subcommand "history"
    #
    cmd_history = subcmds.add_parser(
        'history',
        description=commands.history.__doc__,
        formatter_class=parser.formatter_class,
        help='Display the history of an asset or directory.'
    )
    cmd_history.set_defaults(run=commands.history)
    build_parser(cmd_history, args_history)
    #
    # subcommand "init"
    #
    cmd_init = subcmds.add_parser(
        'init',
        description=commands.init.__doc__,
        formatter_class=parser.formatter_class,
        help='Initialize a new Onyo repository.'
    )
    cmd_init.set_defaults(run=commands.init)
    build_parser(cmd_init, args_init)
    #
    # subcommand "mkdir"
    #
    cmd_mkdir = subcmds.add_parser(
        'mkdir',
        description=commands.mkdir.__doc__,
        formatter_class=parser.formatter_class,
        help='Create directories.'
    )
    cmd_mkdir.set_defaults(run=commands.mkdir)
    build_parser(cmd_mkdir, args_mkdir)
    #
    # subcommand "mv"
    #
    cmd_mv = subcmds.add_parser(
        'mv',
        description=commands.mv.__doc__,
        formatter_class=parser.formatter_class,
        help='Move assets or directories into a destination directory; or rename a directory.'
    )
    cmd_mv.set_defaults(run=commands.mv)
    build_parser(cmd_mv, args_mv)
    #
    # subcommand "new"
    #
    cmd_new = subcmds.add_parser(
        'new',
        description=commands.new.__doc__,
        formatter_class=parser.formatter_class,
        help='Create new assets and populate with key-value pairs.'
    )
    cmd_new.set_defaults(run=commands.new)
    build_parser(cmd_new, args_new)
    #
    # subcommand "rm"
    #
    cmd_rm = subcmds.add_parser(
        'rm',
        description=commands.rm.__doc__,
        formatter_class=parser.formatter_class,
        help='Delete assets and directories.'
    )
    cmd_rm.set_defaults(run=commands.rm)
    build_parser(cmd_rm, args_rm)
    #
    # subcommand "set"
    #
    cmd_set = subcmds.add_parser(
        'set',
        description=commands.set.__doc__,
        formatter_class=parser.formatter_class,
        help='Set the value of keys for assets.'
    )
    cmd_set.set_defaults(run=commands.set)
    build_parser(cmd_set, args_set)
    #
    # subcommand "shell-completion"
    #
    cmd_shell_completion = subcmds.add_parser(
        'shell-completion',
        description=commands.shell_completion.__doc__,
        formatter_class=parser.formatter_class,
        help='Display a tab-completion script for Onyo.'
    )
    cmd_shell_completion.set_defaults(run=commands.shell_completion)
    build_parser(cmd_shell_completion, args_shell_completion)
    #
    # subcommand "tree"
    #
    cmd_tree = subcmds.add_parser(
        'tree',
        description=commands.tree.__doc__,
        formatter_class=parser.formatter_class,
        help='List the assets and directories of a directory in ``tree`` format.'
    )
    cmd_tree.set_defaults(run=commands.tree)
    build_parser(cmd_tree, args_tree)
    #
    # subcommand "unset"
    #
    cmd_unset = subcmds.add_parser(
        'unset',
        description=commands.unset.__doc__,
        formatter_class=parser.formatter_class,
        help='Remove keys from assets.'
    )
    cmd_unset.set_defaults(run=commands.unset)
    build_parser(cmd_unset, args_unset)

    return parser


def get_subcmd_index(arglist, start: int = 1) -> Optional[int]:
    """
    Get the index of the subcommand from a provided list of arguments (usually sys.argv).

    Returns the index on success, and None in failure.
    """
    # TODO: alternatively, this could use TabCompletion._argparse_to_dict()
    # flags which accept an argument
    flagplus = ['-C', '--onyopath']

    try:
        # find the first non-flag argument
        nonflag = next((a for a in arglist[start:] if a[0] != '-'))
        index = arglist.index(nonflag, start)
    except (StopIteration, ValueError):
        return None

    # check if it's the subcommand, or just an argument to a flag
    if arglist[index - 1] in flagplus:
        index = get_subcmd_index(arglist, index + 1)

    return index


def main() -> None:
    # NOTE: this unfortunately-located-hack is to pass uninterpreted args to
    # "onyo config".
    # nargs=argparse.REMAINDER is supposed to do this, but did not work for our
    # needs, and as of Python 3.8 is soft-deprecated (due to being buggy).
    # For more information, see https://docs.python.org/3.10/library/argparse.html#arguments-containing
    passthrough_subcmds = ['config']
    subcmd_index = get_subcmd_index(sys.argv)
    if subcmd_index and sys.argv[subcmd_index] in passthrough_subcmds:
        # display the subcmd's --help, and don't pass it through
        if not any(x in sys.argv for x in ['-h', '--help']):
            sys.argv.insert(subcmd_index + 1, '--')

    global subcmds
    # parse the arguments
    parser = setup_parser()
    args, extras = parser.parse_known_args()
    if extras:
        if args.cmd:
            subcmds._name_parser_map[args.cmd].print_usage(file=sys.stderr)
        parser.error("unrecognized arguments: %s" % " ".join(extras))

    # configure user interface
    ui.set_debug(args.debug)
    ui.set_yes(args.yes)
    ui.set_quiet(args.quiet)

    # run the subcommand
    if subcmd_index:
        old_cwd = Path.cwd()
        os.chdir(args.opdir)
        try:
            args.run(args)
        except Exception as e:
            # TODO: This may need to be nicer, but in any case: Turn any exception/error into a message and exit
            #       non-zero here, in order to have this generic last catcher.
            ui.error(e)
            code = e.returncode if hasattr(e, 'returncode') else 1  # pyre-ignore
            sys.exit(code)
        except KeyboardInterrupt:
            ui.error("User interrupted.")
            sys.exit(1)
        finally:
            os.chdir(old_cwd)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
