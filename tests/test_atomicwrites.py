import os
import errno

from atomicwrites import atomic_write

import pytest


def test_atomic_write(tmpdir):
    fname = tmpdir.join('ha')
    for i in range(2):
        with atomic_write(str(fname), overwrite=True) as f:
            f.write('hoho')

    with pytest.raises(OSError) as excinfo:
        with atomic_write(str(fname), overwrite=False) as f:
            f.write('haha')

    assert excinfo.value.errno == errno.EEXIST

    assert fname.read() == 'hoho'
    assert len(tmpdir.listdir()) == 1


def test_teardown(tmpdir):
    fname = tmpdir.join('ha')
    with pytest.raises(AssertionError):
        with atomic_write(str(fname), overwrite=True):
            assert False

    assert not tmpdir.listdir()


def test_replace_simultaneously_created_file(tmpdir):
    fname = tmpdir.join('ha')
    with atomic_write(str(fname), overwrite=True) as f:
        f.write('hoho')
        fname.write('harhar')
        assert fname.read() == 'harhar'
    assert fname.read() == 'hoho'
    assert len(tmpdir.listdir()) == 1


def test_replace_keep_mode_unchanged(tmpdir):
    fname = tmpdir.join('ha')
    fname.write('abc')
    os.chmod(str(fname), 0640)
    f_mode_before = os.stat(str(fname)).st_mode
    with atomic_write(str(fname), overwrite=True) as f:
        f.write('hoho')
    f_mode_after = os.stat(str(fname)).st_mode
    assert f_mode_before == f_mode_after


def test_dont_remove_simultaneously_created_file(tmpdir):
    fname = tmpdir.join('ha')
    with pytest.raises(OSError) as excinfo:
        with atomic_write(str(fname), overwrite=False) as f:
            f.write('hoho')
            fname.write('harhar')
            assert fname.read() == 'harhar'

    assert excinfo.value.errno == errno.EEXIST
    assert fname.read() == 'harhar'
    assert len(tmpdir.listdir()) == 1


# Verify that nested exceptions during rollback do not overwrite the initial
# exception that triggered a rollback.
def test_open_reraise(tmpdir):
    fname = tmpdir.join('ha')
    with pytest.raises(AssertionError):
        with atomic_write(str(fname), overwrite=False) as f:
            # Mess with f, so rollback will trigger an OSError. We're testing
            # that the initial AssertionError triggered below is propagated up
            # the stack, not the second exception triggered during rollback.
            f.name = "asdf"
            # Now trigger our own exception.
            assert False, "Intentional failure for testing purposes"
