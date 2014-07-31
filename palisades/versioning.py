import atexit
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import time

if platform.system() != 'Windows':
    from shutil import WindowsError

LOGGER = logging.getLogger('versioning')
LOGGER.setLevel(logging.ERROR)

class VCSQuerier(object):
    def _run_command(self, cmd):
        """Run a subprocess.Popen command.  This function is intended for internal
        use only and ensures a certain degree of uniformity across the various
        subprocess calls made in this module.

        cmd - a python string to be executed in the shell.

        Returns a python bytestring of the output of the input command."""
        p = subprocess.Popen(cmd, shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return p.stdout.read().replace('\n', '')

    @property
    def tag_distance(self):
        pass

    @property
    def build_id(self):
        pass

    @property
    def latest_tag(self):
        pass

    @property
    def py_arch(self):
        """This function gets the python architecture string.  Returns a string."""
        return platform.architecture()[0]

    @property
    def release_version(self):
        """This function gets the release version.  Returns either the latest tag
        (if we're on a release tag) or None, if we're on a dev changeset."""
        if self.tag_distance == 0:
            return self.latest_tag
        return None

    @property
    def version(self):
        """This function gets the module's version string.  This will be either the
        dev build ID (if we're on a dev build) or the current tag if we're on a
        known tag.  Either way, the return type is a string."""
        release_version = self.release_version
        if release_version == None:
            return self.build_dev_id(self.build_id)
        return release_version

    def build_dev_id(self, build_id=None):
        """This function builds the dev version string.  Returns a string."""
        if build_id == None:
            build_id = self.build_id
        return 'dev%s' % (build_id)

    def get_architecture_string(self):
        """Return a string representing the operating system and the python
        architecture on which this python installation is operating (which may be
        different than the native processor architecture.."""
        return '%s%s' % (platform.system().lower(),
            platform.architecture()[0][0:2])


class HgRepo(VCSQuerier):
    HG_CALL = 'hg log -r . --config ui.report_untrusted=False'

    @property
    def build_id(self):
        """Call mercurial with a template argument to get the build ID.  Returns a
        python bytestring."""
        cmd = self.HG_CALL + ' --template "{latesttagdistance}:{latesttag} [{node|short}]"'
        return self._run_command(cmd)

    @property
    def tag_distance(self):
        """Call mercurial with a template argument to get the distance to the latest
        tag.  Returns an int."""
        cmd = self.HG_CALL + ' --template "{latesttagdistance}"'
        return int(self._run_command(cmd))

    @property
    def latest_tag(self):
        """Call mercurial with a template argument to get the latest tag.  Returns a
        python bytestring."""
        cmd = self.HG_CALL + ' --template "{latesttag}"'
        return self._run_command(cmd)

class GitRepo(VCSQuerier):
    def __init__(self):
        VCSQuerier.__init__(self)
        self._tag_distance = None
        self._latest_tag = None
        self._commit_hash = None

    def _describe_current_rev(self):
        self._tag_distance = None
        self._latest_tag = None
        self._commit_hash = None

        cmd = 'git describe --abbrev=0 --all'
        data = self._run_command(cmd).replace('tags/', '')

        branch_cmd = 'git rev-parse --abbrev-ref HEAD'
        current_branch = self._run_command(branch_cmd)

        # assume that the tag has no dashes in it
        if data == 'heads/%s' % current_branch:
            # when there are no tags
            self._latest_tag = 'null'

            num_commits_cmd = 'git rev-list %s --count' % current_branch
            self._tag_distance = self._run_command(num_commits_cmd)

            commit_hash_cmd = 'git log -1 --pretty="format:%h"'
            self._commit_hash = self._run_command(commit_hash_cmd)
        elif '-' not in data:
            # then we're at a tag
            self._latest_tag = str(data)
            self._tag_distance = 0

            commit_hash_cmd = 'git log -1 --pretty="format:%h"'
            self._commit_hash = self._run_command(commit_hash_cmd)
        else:
            # we're not at a tag, so data has the format:
            # data = tagname-tagdistange-commit_hash
            tagname, tag_dist, commit_hash = data.split('-')
            self._tag_distance = tagname
            self._latest_tag = tagname
            self._commit_hash = commit_hash

    @property
    def build_id(self):
        self._describe_current_rev()
        return "%s:%s [%s]" % (self._tag_distance, self._latest_tag,
            self._commit_hash)

    @property
    def tag_distance(self):
        self._describe_current_rev()
        return self._tag_distance

    @property
    def latest_tag(self):
        self._describe_current_rev()
        return self._latest_tag

REPO = GitRepo()

def build_data():
    """Returns a dictionary of relevant build data."""
    data = {
        'release': REPO.latest_tag,
        'build_id': REPO.build_id,
        'py_arch': REPO.py_arch,
        'version_str': REPO.version
    }
    return data

def write_build_info(source_file_uri):
    """Write the build information to the file specified as `source_file_uri`.
    """
    temp_file_uri = _temporary_filename()
    temp_file = open(temp_file_uri, 'w+')

    source_file = open(os.path.abspath(source_file_uri))
    for line in source_file:
        if line == "__version__ = 'dev'\n":
            temp_file.write("__version__ = '%s'\n" % REPO.version)
        elif line == "build_data = None\n":
            build_information = build_data()
            temp_file.write("build_data = %s\n" % str(build_information.keys()))
            for key, value in sorted(build_information.iteritems()):
                temp_file.write("%s = '%s'\n" % (key, value))
        else:
            temp_file.write(line)
    temp_file.flush()
    temp_file.close()

    source_file.close()
    source_file_removed = False
    for index in range(10):
        try:
            os.remove(source_file_uri)
            source_file_removed = True
        except WindowsError:
            time.sleep(0.25)
    if not source_file_removed:
        raise IOError('Could not remove %s' % source_file_uri)

    # This whole block of try/except logic is an attempt to mitigate a problem
    # we've experienced on Windows, where a file had not quite been deleted
    # before we tried to copy the new file over the old one.
    file_copied = False
    for index in range(10):
        try:
            shutil.copyfile(temp_file_uri, source_file_uri)
            file_copied = True
            break  # if we successfully copy, end the loop.
        except WindowsError:
            time.sleep(0.25)

    if not file_copied:
        raise IOError('Could not copy %s to %s', temp_file_uri,
            source_file_uri)

def _temporary_filename():
    """Returns a temporary filename using mkstemp. The file is deleted
        on exit using the atexit register.  This function was migrated from
        the invest-3 raster_utils file, rev 11354:1029bd49a77a.

        returns a unique temporary filename"""

    file_handle, path = tempfile.mkstemp()
    os.close(file_handle)

    def remove_file(path):
        """Function to remove a file and handle exceptions to register
            in atexit"""
        try:
            os.remove(path)
        except OSError as exception:
            #This happens if the file didn't exist, which is okay because maybe
            #we deleted it in a method
            pass

    atexit.register(remove_file, path)
    return path



