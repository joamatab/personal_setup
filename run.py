import functools
import subprocess
import textwrap
from pathlib import Path


def blue_print(arg):
    print("\033[1;34m{}\033[0m".format(arg))


def pretty_name(fn):
    return " ".join(fn.__name__.split("_")).title()


def run(cmd, verbose=True):
    if verbose:
        blue_print(cmd)
    proc = subprocess.Popen(
        cmd, bufsize=1, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=Path(__file__).parent, universal_newlines=True
    )
    while True:
        if verbose:
            out = proc.stdout.readline()
            print(textwrap.indent(out, "\t"), end="")
            if out:
                continue
        if proc.poll() is not None:
            break
    return proc.poll()


fns = []


def collect(fn):
    global fns
    fns.append(fn)
    return fn


def skip_if(cmd, should_fail=False, should_raise=False):
    def decorator(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            returncode = run(cmd, verbose=False)
            command_failed = bool(returncode)
            if should_fail:
                command_failed = not command_failed
            if command_failed:
                fn(*args, **kwargs)
            elif should_raise:
                raise subprocess.CalledProcessError(returncode, cmd)
            else:
                blue_print("=" * 25)
                blue_print("Skipping installing " + pretty_name(fn) + "...")
                blue_print("=" * 25)
                print()
        return inner
    return decorator


skip_if_fail = functools.partial(skip_if, should_fail=True)
raise_if_fail = functools.partial(skip_if, should_fail=True, should_raise=True)


def sh(check=True):
    def decorator(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            blue_print("=" * 25)
            blue_print("Installing " + pretty_name(fn) + "...")
            blue_print("=" * 25)
            print()
            print("Enter to continue (or type something to skip)... ", end="")
            if input():
                return
            lines = fn(*args, **kwargs).splitlines()
            for l in lines:
                cmd = l.strip()
                if not cmd:
                    continue
                returncode = run(cmd)
                if check and returncode:
                    print("\n")
                    raise subprocess.CalledProcessError(returncode, cmd)
            print()
        return inner
    return decorator


# ==========================
# The actual setup begins...
# ==========================


@collect
@sh()
def zsh():
    return """
    [[ ! -f ~/.zshenv ]] || diff zshenv ~/.zshenv
    cp zshenv ~/.zshenv
    [[ ! -f ~/.zshrc ]] || diff zshrc ~/.zshrc
    cp zshrc ~/.zshrc
    rm -rf ~/.zgen
    git clone https://github.com/tarjoilija/zgen.git ~/.zgen
    zsh -i -c ''
    [[ $SHELL = "$(which zsh)" ]] || chsh -s $(which zsh)
    """


@collect
@sh()
def vim():
    return """
    [[ ! -f ~/.vimrc ]] || diff vimrc ~/.vimrc
    cp vimrc ~/.vimrc
    curl -fLo ~/.vim/autoload/plug.vim --create-dirs https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim
    rm -rf ~/.vim/.swp
    mkdir ~/.vim/.swp
    """


@collect
@skip_if("which brew")
@sh()
def brew():
    return '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"'


@collect
@skip_if_fail("which brew")
@sh()
def main_brew_stuff():
    return """
    brew install python3
    brew install ripgrep
    brew install fzf
    brew install pipx
    brew install pyenv
    brew install htop
    brew install tree
    """


@collect
@skip_if_fail("which brew")
@sh()
def provisional_brew_stuff():
    return """
    brew install fd
    brew install bat
    brew install tokei
    brew install hyperfine
    brew install dust
    brew install gh
    """


@collect
@skip_if_fail("brew cask doctor")
@sh()
def brew_casks():
    return """
    brew cask install atom
    brew cask install basictex
    brew cask install firefox
    brew cask install google-chrome
    brew cask install hammerspoon
    brew cask install spotify
    """


@collect
@skip_if_fail("brew cask doctor | grep hammerspoon")
@sh()
def hammerspoon_config():
    return """
    rm -rf ~/.hammerspoon
    mkdir ~/.hammerspoon
    cp hammerspoon.lua ~/.hammerspoon/init.lua
    """


@collect
@skip_if_fail("which apm")
@sh()
def apm():
    return "apm install sync-settings"


@collect
@raise_if_fail("which python3")
@sh()
def python_libraries():
    return """
    python3 -m pip install aiohttp
    python3 -m pip install beautifulsoup4
    python3 -m pip install pandas
    python3 -m pip install python-dateutil

    python3 -m pip install ipdb
    python3 -m pip install ipython
    """


@collect
@raise_if_fail("which pipx")
@sh()
def python_tools():
    return """
    pipx install black
    pipx install flake8
    pipx inject flake8 flake8-pyi flake8-bugbear
    pipx install git-revise
    pipx install isort
    pipx install mypy
    pipx install poetry
    pipx install pyinstrument
    pipx install pylint
    pipx install pypyp
    pipx install pytest
    pipx inject pytest pytest-cov pytest-xdist
    pipx install tox
    """


if __name__ == "__main__":
    for fn in fns:
        fn()
