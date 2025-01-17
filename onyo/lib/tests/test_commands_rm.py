import pytest

from onyo.lib.exceptions import InvalidInventoryOperationError, InventoryOperationError
from onyo.lib.inventory import Inventory
from onyo.lib.onyo import OnyoRepo
from ..commands import onyo_rm


@pytest.mark.ui({'yes': True})
def test_onyo_rm_errors(inventory: Inventory) -> None:
    """`onyo_rm` must raise the correct error in different illegal or impossible calls."""
    # delete non-existing asset
    pytest.raises(InvalidInventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / "TYPE_MAKER_MODEL.SERIAL",
                  message="some subject\n\nAnd a body")

    # delete non-existing directory
    pytest.raises(InvalidInventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / "somewhere" / "non-existing",
                  message="some subject\n\nAnd a body")

    # delete .anchor
    pytest.raises(InvalidInventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / OnyoRepo.ANCHOR_FILE_NAME,
                  message="some subject\n\nAnd a body")

    # delete outside onyo repository
    pytest.raises(InventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / "..",
                  message="some subject\n\nAnd a body")

    # deleting an existing file which is neither an asset nor a directory is illegal
    assert (inventory.root / ".onyo" / "templates" / "laptop.example").is_file()
    pytest.raises(InvalidInventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / ".onyo" / "templates" / "laptop.example",
                  message="some subject\n\nAnd a body")

    # delete inventory root
    pytest.raises(InvalidInventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root,
                  message="some subject\n\nAnd a body")

    # delete dir in mode 'asset'
    pytest.raises(ValueError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / "somewhere",
                  mode="asset",
                  message="some subject\n\nAnd a body")

    # delete asset in mode 'dir'
    pytest.raises(ValueError,
                  onyo_rm,
                  inventory,
                  paths=inventory.root / "somewhere" / "nested" / "TYPE_MAKER_MODEL.SERIAL",
                  mode="dir",
                  message="some subject\n\nAnd a body")

    # no error scenario leaves the git tree unclean
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
def test_onyo_rm_errors_before_rm(inventory: Inventory) -> None:
    """`onyo_rm` must raise the correct error and is not allowed to delete anything if one of
    the paths does not exist.
    """
    asset_path = inventory.root / "somewhere" / "nested" / "TYPE_MAKER_MODEL.SERIAL"
    destination_path = inventory.root / 'empty'
    old_hexsha = inventory.repo.git.get_hexsha()

    # one of multiple paths to delete does not exist
    pytest.raises(InvalidInventoryOperationError,
                  onyo_rm,
                  inventory,
                  paths=[asset_path, inventory.root / "not-existent", destination_path],
                  message="some subject\n\nAnd a body")

    # nothing was deleted and no new commit was created
    assert asset_path.is_file()
    assert destination_path.is_dir()
    # no commit was added
    assert inventory.repo.git.get_hexsha() == old_hexsha
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
@pytest.mark.repo_dirs("a/b/c", "a/b/c/c")
def test_onyo_rm_with_same_input_path_twice(inventory: Inventory) -> None:
    """`onyo rm` should not fail when the same path is implied for removal multiple times."""
    asset_path = inventory.root / "somewhere" / "nested" / "TYPE_MAKER_MODEL.SERIAL"
    old_hexsha = inventory.repo.git.get_hexsha()

    # delete a path through giving it twice with the same name to onyo_rm()
    onyo_rm(inventory,
            paths=[asset_path, asset_path],
            message="some subject\n\nAnd a body")

    # asset file
    assert not asset_path.exists()
    assert asset_path not in inventory.repo.git.files
    # exactly one commit added
    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()

    # delete same dir twice implicitly
    old_hexsha = inventory.repo.git.get_hexsha()
    abc = inventory.root / "a/b/c"
    abcc = inventory.root / "a/b/c/c"
    assert inventory.repo.is_inventory_dir(abcc)
    assert inventory.repo.is_inventory_dir(abc)
    onyo_rm(inventory,
            paths=[abc, abcc],
            message="some subject\n\nAnd a body")
    assert not abcc.exists()
    assert not abc.exists()
    # exactly one commit added
    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
def test_onyo_rm_move_single(inventory: Inventory) -> None:
    """Delete a single asset path."""
    asset_path = inventory.root / "somewhere" / "nested" / "TYPE_MAKER_MODEL.SERIAL"
    old_hexsha = inventory.repo.git.get_hexsha()

    # delete a single asset as path
    onyo_rm(inventory,
            paths=asset_path,
            message="some subject\n\nAnd a body")

    # asset was deleted
    assert not asset_path.exists()
    assert asset_path not in inventory.repo.git.files
    # exactly one commit added
    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
def test_onyo_rm_delete_directory(inventory: Inventory) -> None:
    """Delete a single directory path."""
    dir_path = inventory.root / 'empty'
    old_hexsha = inventory.repo.git.get_hexsha()

    # delete a single asset as path
    onyo_rm(inventory,
            paths=dir_path,
            message="some subject\n\nAnd a body")

    # directory was deleted
    assert not dir_path.exists()
    assert dir_path / OnyoRepo.ANCHOR_FILE_NAME not in inventory.repo.git.files
    # exactly one commit added
    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
def test_onyo_rm_list(inventory: Inventory) -> None:
    """Delete a directory and an asset together as a list in one commit."""
    asset_path = inventory.root / "somewhere" / "nested" / "TYPE_MAKER_MODEL.SERIAL"
    dir_path = inventory.root / 'empty'
    old_hexsha = inventory.repo.git.get_hexsha()

    # delete an asset and a dir together in the same call
    onyo_rm(inventory,
            paths=[asset_path, dir_path],
            message="some subject\n\nAnd a body")

    # asset was deleted
    assert not asset_path.exists()
    assert asset_path not in inventory.repo.git.files
    # dir was deleted
    assert not dir_path.exists()
    assert dir_path / OnyoRepo.ANCHOR_FILE_NAME not in inventory.repo.git.files
    # exactly one commit added
    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
def test_onyo_rm_subpath_and_contents(inventory: Inventory) -> None:
    """Delete a directory with contents."""
    asset_path = inventory.root / "somewhere" / "nested" / "TYPE_MAKER_MODEL.SERIAL"
    nested = inventory.root / "somewhere" / "nested"
    old_hexsha = inventory.repo.git.get_hexsha()

    # delete a path
    onyo_rm(inventory,
            paths=nested,
            message="some subject\n\nAnd a body")

    # "somewhere" NOT deleted
    assert (inventory.root / "somewhere").is_dir
    assert (inventory.root / "somewhere" / OnyoRepo.ANCHOR_FILE_NAME) in inventory.repo.git.files
    # dir "nested" was deleted, and it's contents, too
    assert not nested.exists()
    assert (nested / OnyoRepo.ANCHOR_FILE_NAME) not in inventory.repo.git.files
    assert not asset_path.exists()
    assert asset_path not in inventory.repo.git.files
    # exactly one commit added
    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()


@pytest.mark.ui({'yes': True})
def test_onyo_rm_asset_dir(inventory: Inventory) -> None:

    inventory.add_asset(dict(some_key="some_value",
                             type="TYPE",
                             make="MAKE",
                             model="MODEL",
                             serial="SERIAL2",
                             other=1,
                             directory=inventory.root,
                             is_asset_directory=True)
                        )
    asset_dir = inventory.root / "TYPE_MAKE_MODEL.SERIAL2"
    inventory.commit("add an asset dir")

    old_hexsha = inventory.repo.git.get_hexsha()

    # remove entirely
    onyo_rm(inventory,
            paths=asset_dir,
            mode="all",
            message="Remove asset dir completely")

    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()
    assert not asset_dir.exists()

    inventory.repo.git._git(['reset', '--hard', 'HEAD~1'])
    inventory.repo.clear_caches()
    # remove asset aspect only
    onyo_rm(inventory,
            paths=asset_dir,
            mode="asset",
            message="Remove asset aspect")

    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()
    assert inventory.repo.is_inventory_dir(asset_dir)
    assert not inventory.repo.is_asset_path(asset_dir)

    inventory.repo.git._git(['reset', '--hard', 'HEAD~1'])
    inventory.repo.clear_caches()
    # remove dir aspect only
    onyo_rm(inventory,
            paths=asset_dir,
            mode="dir",
            message="Remove asset aspect")

    assert inventory.repo.git.get_hexsha('HEAD~1') == old_hexsha
    assert inventory.repo.git.is_clean_worktree()
    assert not inventory.repo.is_inventory_dir(asset_dir)
    assert inventory.repo.is_asset_path(asset_dir)
