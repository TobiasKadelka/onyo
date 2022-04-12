import subprocess
import logging
import os
import sys
import shlex


from git import Repo, exc

logging.basicConfig()
logger = logging.getLogger('onyo')


def run_cmd(cmd, comment=""):
    if comment != "":
        run_process = subprocess.Popen(shlex.split(cmd) + [comment],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
    else:
        run_process = subprocess.Popen(shlex.split(cmd),
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       universal_newlines=True)
    run_output, run_error = run_process.communicate()
    if (run_error != ""):
        logger.error(run_error)
        sys.exit(1)
    else:
        logger.debug(cmd + " " + comment)
    return run_output


# checks if a given path is git-directory (needs to be main-level)
def is_git_dir(directory):
    try:
        Repo(directory).git_dir
        return True
    except exc.InvalidGitRepositoryError:
        return False


def get_git_root(path):
    # first checks if file is in git from current position
    try:
        git_repo = Repo(path, search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")
        if os.path.isdir(os.path.join(git_root, ".onyo")):
            return git_root
        else:
            raise exc.InvalidGitRepositoryError
    # otherwise checks if given file relative to $ONYO_REPOSITORY_DIR is in a
    # git repository
    except (exc.NoSuchPathError, exc.InvalidGitRepositoryError):
        onyo_path = os.environ.get('ONYO_REPOSITORY_DIR')
        if onyo_path is None:
            logger.error(path + " is no onyo repository.")
            sys.exit(1)
        elif not is_git_dir(onyo_path):
            logger.error(path + " is no onyo repository.")
            sys.exit(1)

        git_repo = Repo(os.path.join(path, onyo_path),
                        search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")
        return git_root


def get_full_filepath(git_directory, file):
    full_filepath = os.path.join(git_directory, file)
    if not os.path.exists(full_filepath):
        full_filepath = os.path.join(git_directory, os.getcwd())
        full_filepath = os.path.join(full_filepath, file)
    if not os.path.exists(full_filepath):
        logger.error(file + " not found.")
        sys.exit(1)
    return full_filepath


def get_editor():
    editor = os.environ.get('EDITOR')
    if editor is None:
        editor = 'nano'
    return editor


def edit_file(file):
    if not os.path.isfile(file):
        logger.error(file + " does not exist.")
        sys.exit(1)
    os.system(get_editor() + " \"" + file + "\"")
    return


def build_git_add_cmd(directory, file):
    return "git -C \"" + directory + "\" add \"" + file + "\""


def prepare_directory(directory):
    if os.path.isdir(os.path.join(os.getcwd(), directory)):
        location = os.path.join(os.getcwd(), directory)
    elif os.environ.get('ONYO_REPOSITORY_DIR') is not None and os.path.isdir(os.path.join(os.environ.get('ONYO_REPOSITORY_DIR'), directory)) and os.path.isdir(os.path.join(get_git_root(directory), directory)):
        location = os.path.join(get_git_root(directory), directory)
    else:
        logger.error(directory + " does not exist.")
        sys.exit(1)
    return location
