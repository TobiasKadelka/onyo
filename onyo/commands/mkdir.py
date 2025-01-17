from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from onyo import OnyoRepo
from onyo.argparse_helpers import path
from onyo.lib.commands import onyo_mkdir
from onyo.lib.inventory import Inventory
from onyo.shared_arguments import shared_arg_message

if TYPE_CHECKING:
    import argparse

args_mkdir = {
    'directory': dict(
        metavar='DIR',
        nargs='+',
        type=path,
        help="""
            Directories to create; or assets to convert into an Asset Directory.
        """
    ),

    'message': shared_arg_message,
}


def mkdir(args: argparse.Namespace) -> None:
    """
    Create **DIRECTORY**\s or convert Asset Files into an Asset Directory.

    Intermediate directories are created as needed (i.e. parent and child
    directories can be created in one call).

    An empty ``.anchor`` file is added to each directory, to ensure that git
    tracks them even when empty.

    If the **DIRECTORY** already exists, the path is protected, or the asset is
    already an Asset Directory, then Onyo will error and leave everything
    unmodified.
    """
    dirs = [Path(d).resolve() for d in args.directory]
    inventory = Inventory(repo=OnyoRepo(Path.cwd(), find_root=True))
    onyo_mkdir(inventory,
               dirs=dirs,
               message='\n\n'.join(m for m in args.message) if args.message else None)
