import subprocess
from pathlib import Path
from typing import List

import pytest

from onyo.lib import OnyoRepo

directories = ['.',
               'simple',
               's p a c e s',
               's p a/c e s',
               'r/e/c/u/r/s/i/v/e',
               'very/very/very/deep'
               ]
asset_specs = [{'type': 'laptop',
                'make': 'apple',
                'model': 'macbookpro'},
               {'type': 'lap top',
                'make': 'ap ple',
                'model': 'mac book pro'}
               ]

assets = []
for i, d in enumerate(directories):
    for spec in asset_specs:
        spec['serial'] = str(i)
        name = f"{spec['type']}_{spec['make']}_{spec['model']}.{spec['serial']}"
        content = "\n".join(f"{key}: {value}" for key, value in spec.items())
        assets.append([f"{d}/{name}", content])

asset_paths = [a[0] for a in assets]

values = [["mode=single"],
          ["mode=double"], ["key=space bar"]]

non_existing_assets: List[List[str]] = [
    ["single_non_existing.asset"],
    ["simple/single_non_existing.asset"],
    [asset_paths[0], "single_non_existing.asset"]]

name_fields = [["type=desktop"],
               ["make=lenovo"],
               ["model=thinkpad"],
               ["serial=1234"],
               ["type=surface"], ["make=microsoft"], ["model=go"], ["serial=666"],
               ["key=value"], ["type=server"], ["other=content"], ["serial=777"],
               ["serial=faux"], ["different=value"]]


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', asset_paths)
@pytest.mark.parametrize('set_values', values)
def test_set(repo: OnyoRepo,
             asset: str,
             set_values: list[str]) -> None:
    """Test that `onyo set KEY=VALUE <asset>` updates contents of assets."""
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', *set_values, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # verify changes, and the repository clean
    for value in set_values:
        assert value.replace("=", ": ") in Path.read_text(Path(asset))
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
@pytest.mark.parametrize('set_values', values)
def test_set_interactive(repo: OnyoRepo,
                         asset: str,
                         set_values: list[str]) -> None:
    """Test that `onyo set KEY=VALUE <asset>` updates contents of assets."""
    ret = subprocess.run(['onyo', 'set', '--keys', *set_values, '--path', asset],
                         input='y', capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert "Update assets? (y/n) " in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # verify changes, and the repository clean
    for value in set_values:
        assert value.replace("=", ": ") in Path.read_text(Path(asset))
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('set_values', values)
def test_set_multiple_assets(repo: OnyoRepo,
                             set_values: list[str]) -> None:
    """Test that `onyo set KEY=VALUE <asset>` can update the contents of multiple
    assets in a single call.
    """
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', *set_values,
                          '--path', *asset_paths],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # verify that all assets are in output and updated, and the repository clean
    for asset in asset_paths:
        assert str(Path(asset)) in ret.stdout
        for value in set_values:
            assert value.replace("=", ": ") in Path.read_text(Path(asset))
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('no_assets', non_existing_assets)
def test_set_error_non_existing_assets(repo: OnyoRepo,
                                       no_assets: list[str]) -> None:
    """Test that `onyo set KEY=VALUE <asset>` errors correctly for:
    - non-existing assets on root
    - non-existing assets in directories
    - one non-existing asset in a list of existing ones
    """
    ret = subprocess.run(['onyo', 'set', '--keys', 'key=value',
                          '--path', *no_assets], capture_output=True, text=True)

    # verify output and the state of the repository
    assert not ret.stdout
    assert "The following paths aren't assets:" in ret.stderr
    assert ret.returncode == 1
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('set_values', values)
def test_set_without_path(repo: OnyoRepo,
                          set_values: list[str]) -> None:
    """Test that `onyo set KEY=VALUE` without a given path fails.
    """
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', *set_values],
                         capture_output=True, text=True)

    assert ret.returncode != 0
    assert "Usage:" in ret.stderr  # argparse should already complain
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
@pytest.mark.parametrize('set_values', values)
def test_set_discard_changes_single_assets(repo: OnyoRepo,
                                           asset: str,
                                           set_values: list[str]) -> None:
    """Test that `onyo set` discards changes for assets successfully."""
    ret = subprocess.run(['onyo', 'set', '--keys', *set_values, '--path', asset],
                         input='n',
                         capture_output=True, text=True)

    # verify output for just dot, should be all in onyo root, but not recursive
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert "No assets updated." in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # verify that changes are in output, but not written into the asset
    for value in set_values:
        assert f"+{value.replace('=', ': ')}" in ret.stdout
        assert value.replace("=", ": ") not in Path.read_text(Path(asset))
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
@pytest.mark.parametrize('set_values', [values[0]])
def test_set_message_flag(repo: OnyoRepo,
                          asset: str,
                          set_values: list[str]) -> None:
    """Test that `onyo set --message msg` overwrites the
    default commit message with one specified by the user
    containing various special characters.
    """
    msg = "I am here to test the --message flag with spe\"cial\\char\'acteஞrs!"
    ret = subprocess.run(['onyo', '--yes', 'set', '--message', msg,
                          '--keys', *set_values, '--path', asset],
                         capture_output=True, text=True)
    assert ret.returncode == 0
    assert not ret.stderr

    # test that the onyo history does contain the user-defined message
    ret = subprocess.run(['onyo', 'history', '-I'], capture_output=True, text=True)
    assert msg in ret.stdout
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
def test_add_new_key_to_existing_content(repo: OnyoRepo,
                                         asset: str) -> None:
    """Test that `onyo set KEY=VALUE <asset>` can be called two times with
    different `KEY`, and adds it without overwriting existing values.
    """
    set_1 = "change=one"
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', set_1, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert set_1.replace("=", ": ") in ret.stdout
    assert set_1.replace("=", ": ") in Path.read_text(Path(asset))
    assert not ret.stderr
    assert ret.returncode == 0

    # call again and add a different KEY, without overwriting existing contents
    set_2 = "different=key"
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', set_2, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert set_2.replace("=", ": ") in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # This line is unchanged, it should still be the file.
    # Whether and how it shows up in the output depends on how a diff is shown.
    assert set_1.replace("=", ": ") in Path.read_text(Path(asset))
    # this change is new, it has to be part of the diff in the output and the file
    assert set_2.replace("=", ": ") in ret.stdout
    assert set_2.replace("=", ": ") in Path.read_text(Path(asset))

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
def test_set_overwrite_key(repo: OnyoRepo,
                           asset: str) -> None:
    """
    Test that `onyo set KEY=VALUE <asset>` can be called two times with
    different VALUE for the same KEY, and overwrites existing values correctly.
    """
    set_value = "value=original"
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', set_value, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert set_value.replace("=", ": ") in ret.stdout
    assert set_value.replace("=", ": ") in Path.read_text(Path(asset))
    assert not ret.stderr
    assert ret.returncode == 0

    # call again with same key, but different value
    set_value_2 = "value=updated"
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', set_value_2, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert f"-{set_value}".replace("=", ": ") in ret.stdout
    assert f"+{set_value_2}".replace("=", ": ") in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # check that the second value is set in asset
    assert set_value_2.replace("=", ": ") in Path.read_text(Path(asset))

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
def test_setting_new_values_if_some_values_already_set(repo: OnyoRepo,
                                                       asset: str) -> None:
    """Test that `onyo set KEY=VALUE <asset>` updates contents of assets and adds
    the correct output if called multiple times, and that the output is correct.
    """
    set_values = "change=one"
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', set_values, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert set_values.replace("=", ": ") in Path.read_text(Path(asset))
    assert not ret.stderr
    assert ret.returncode == 0

    # call with two values, one of which is already set and should not appear
    # again in the output.
    set_values = ["change=one", "different=key"]
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', *set_values, '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # This line is unchanged, it should still be the file.
    # Whether and how it shows up in the output depends on how a diff is shown.
    assert "change=one".replace("=", ": ") in Path.read_text(Path(asset))

    # this change is new, it has to be in the output
    assert "different=key".replace("=", ": ") in ret.stdout
    assert "different=key".replace("=", ": ") in Path.read_text(Path(asset))

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(assets[0])
@pytest.mark.parametrize('asset', [asset_paths[0]])
@pytest.mark.parametrize('set_values', values)
def test_values_already_set(repo: OnyoRepo,
                            asset: str,
                            set_values: list[str]) -> None:
    """Test that `onyo set KEY=VALUE <asset>` updates
    contents of assets once, and if called again with
    same valid values the command does display the correct
    info message without error, and the repository stays
    in a clean state.
    """

    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', *set_values,
                          '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert str(Path(asset)) in ret.stdout
    for value in set_values:
        assert value.replace("=", ": ") in Path.read_text(Path(asset))
    assert not ret.stderr
    assert ret.returncode == 0

    # call `onyo set` again with the same values
    ret = subprocess.run(['onyo', '--yes', 'set', '--keys', *set_values, '--path', asset],
                         capture_output=True, text=True)

    # verify second output
    assert "No assets updated." in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
@pytest.mark.parametrize('asset', [asset_paths[0]])
@pytest.mark.parametrize('set_values', name_fields)
def test_set_update_name_fields(repo: OnyoRepo,
                                asset: str,
                                set_values: list[str]) -> None:
    """Test that `onyo set --rename --keys KEY=VALUE <asset>` can
    successfully change the names of assets, when KEY is
    type, make, model or/and serial number. Test also, that
    faux serials can be set and name fields are recognized
    and can be updated when they are `onyo set` together
    with a list of content fields.
    """
    ret = subprocess.run(['onyo', '--yes', 'set', '--rename', '--keys', *set_values,
                          '--path', asset], capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert not ret.stderr
    assert ret.returncode == 0

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(*assets)
def test_update_many_faux_serial_numbers(repo: OnyoRepo) -> None:
    """Test that `onyo set --rename serial=faux <asset>`
    can successfully update many assets with new faux
    serial numbers in one call.
    """

    pytest.skip("TODO: faux serials not yet considered outside new. Needs to move (modify_asset)")
    # remember old assets before renaming
    old_asset_names = repo.asset_paths
    ret = subprocess.run(['onyo', '--yes', 'set', '--rename', '--keys',
                          'serial=faux', '--path', *asset_paths], capture_output=True, text=True)

    # verify output
    assert "The following assets will be changed:" in ret.stdout
    assert len(asset_paths) == ret.stdout.count('.faux')
    assert not ret.stderr
    assert ret.returncode == 0

    # this does not work when called in set.py or onyo.py, because this test
    # function still has its own repo object, which does not get updated when
    # calling `onyo set` with subprocess.run()
    repo.clear_caches()

    # verify that the name fields were not added to the contents and the names
    # are actually new
    for file in repo.asset_paths:
        contents = Path.read_text(Path(file))
        assert file not in old_asset_names
        assert "faux" not in contents

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()


@pytest.mark.repo_contents(assets[0])
@pytest.mark.parametrize('asset', [asset_paths[0]])
@pytest.mark.parametrize('set_values', values)
def test_duplicate_keys(repo: OnyoRepo,
                        asset: str,
                        set_values: list[str]) -> None:
    """Test that `onyo set` fails, if the same key is given multiple times."""

    ret = subprocess.run(['onyo', '--yes', 'set', '--keys',
                          *set_values, 'dup_key=1', 'dup_key=2', '--path', asset],
                         capture_output=True, text=True)

    # verify output
    assert ret.returncode == 1
    assert "Keys must not be given multiple times." in ret.stderr
    assert not ret.stdout

    # verify state of repo is clean
    assert repo.git.is_clean_worktree()
