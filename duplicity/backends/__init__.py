"""
Contains all backends in their respective modules.

This module is responsible for loading all available
sub-modules. Users need only import this module, unless they want to
specifically refer to a particular backend.
"""

import duplicity.backends.botobackend
import duplicity.backends.ftpbackend
import duplicity.backends.hsibackend
import duplicity.backends.localbackend
import duplicity.backends.rsyncbackend
import duplicity.backends.sshbackend
import duplicity.backends.webdavbackend





