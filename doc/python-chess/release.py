#!/usr/bin/python3
# Helper script to create and publish a new python-chess release.

import os
import chess
import sys
import subprocess


def system(command):
    print(command)
    exit_code = os.system(command)
    if exit_code != 0:
        sys.exit(exit_code)


def check_git():
    print("--- CHECK GIT ----------------------------------------------------")
    system("git diff --exit-code")
    system("git diff --cached --exit-code")

    system("git fetch origin")
    behind = subprocess.check_output(["git", "rev-list", "--count", "master..origin/master"])
    if int(behind) > 0:
        print("master is {} commits behind origin/master".format(int(behind)))
        sys.exit(1)

def test():
    print("--- TEST ---------------------------------------------------------")
    system("tox --skip-missing-interpreters")


def check_changelog():
    print("--- CHECK CHANGELOG ----------------------------------------------")
    with open("CHANGELOG.rst", "r") as changelog_file:
        changelog = changelog_file.read()

    if "Upcoming in the next release" in changelog:
        print("Found: Upcoming in the next release")
        sys.exit(1)

    tagname = "v{}".format(chess.__version__)
    if tagname not in changelog:
        print("Not found: {}".format(tagname))
        sys.exit(1)


def check_docs():
    print("--- CHECK DOCS ---------------------------------------------------")
    system("python3 setup.py --long-description | rst2html --strict --no-raw > /dev/null")


def tag_and_push():
    print("--- TAG AND PUSH -------------------------------------------------")
    tagname = "v{}".format(chess.__version__)
    release_filename = "release-{}.txt".format(tagname)

    if not os.path.exists(release_filename):
        print(">>> Creating {} ...".format(release_filename))
        first_section = False
        prev_line = None
        with open(release_filename, "w") as release_txt, open("CHANGELOG.rst", "r") as changelog_file:
            headline = "python-chess {}".format(tagname)
            release_txt.write(headline + os.linesep)

            for line in changelog_file:
                if not first_section:
                    if line.startswith("-------"):
                        first_section = True
                else:
                    if line.startswith("-------"):
                        break
                    else:
                        if not prev_line.startswith("------"):
                            release_txt.write(prev_line)

                prev_line = line

    with open(release_filename, "r") as release_txt:
        release = release_txt.read().strip() + os.linesep
        print(release)

    with open(release_filename, "w") as release_txt:
        release_txt.write(release)

    guessed_tagname = input(">>> Sure? Confirm tagname: ")
    if guessed_tagname != tagname:
        print("Actual tagname is: {}".format(tagname))
        sys.exit(1)

    system("git tag {} -s -F {}".format(tagname, release_filename))
    system("git push --atomic origin master {}".format(tagname))
    return tagname


def pypi():
    print("--- PYPI ---------------------------------------------------------")
    system("python3 setup.py sdist bdist_wheel")
    system("twine check dist/*")
    system("twine upload --skip-existing --sign dist/*")


def github_release(tagname):
    print("--- GITHUB RELEASE -----------------------------------------------")
    print("https://github.com/niklasf/python-chess/releases/new?tag={}".format(tagname))


if __name__ == "__main__":
    check_docs()
    test()
    check_git()
    check_changelog()
    tagname = tag_and_push()
    pypi()
    github_release(tagname)
