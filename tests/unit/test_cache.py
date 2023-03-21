import shutil
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

import juju_spell
from juju_spell.cache import AVALIABLE_BACKENDS, DEFAULT_CACHE_BACKEND, Cache, use_cache
from juju_spell.exceptions import JujuSpellError


@pytest.fixture(scope="session")
def tmp_cache_dir():
    # don't use tempfile / tmp_path_dir to increase test coverage
    tmp_cache_dir = Path("/tmp/test-cache")
    Cache.cache_directory = tmp_cache_dir
    yield tmp_cache_dir
    shutil.rmtree(tmp_cache_dir)


def test_00_file_cache_normal(tmp_cache_dir):
    """Test file cache class under normal situation."""
    file_cache = use_cache(DEFAULT_CACHE_BACKEND)
    file_cache.cache_directory = tmp_cache_dir

    # test put
    key1 = "key1"
    value1 = {"name": "foo"}
    file_cache.put(key1, value1)
    cache_file1 = tmp_cache_dir / key1
    assert cache_file1.exists()

    # test get
    data = file_cache.get(key1)["data"]
    timestamp = file_cache.get(key1)["timestamp"]
    assert data == value1
    assert timestamp

    # test delete
    file_cache.delete(key1)
    assert not cache_file1.exists()


@patch.object(juju_spell.cache.FileCache, "_check_expired")
def test_01_file_cache_get(mock_check_expired, tmp_cache_dir):
    """Test file cache get method."""
    file_cache = use_cache(DEFAULT_CACHE_BACKEND)
    file_cache.cache_directory = tmp_cache_dir

    # create some data
    key = "key"
    value = {"name": "foo"}
    file_cache.put(key, value)
    cache_file = tmp_cache_dir / key
    assert cache_file.exists()

    # test get: expire cache
    data = file_cache.get(key)
    assert not data
    assert not cache_file.exists()

    # test get: no key
    data = file_cache.get("random_key")
    assert not data

    # test get: permission denied
    file_cache.put(key, value)
    with patch("builtins.open", new_callable=mock_open) as fake_open:
        fake_open.side_effect = PermissionError()
        with pytest.raises(JujuSpellError, match="permission denied to read from file "):
            file_cache.get(key)

    # test get: general error
    with patch("builtins.open", new_callable=mock_open) as fake_open:
        fake_open.side_effect = Exception()
        with pytest.raises(JujuSpellError):
            file_cache.get(key)


def test_02_file_cache_put(tmp_cache_dir):
    """Test file cache put method."""
    file_cache = use_cache(DEFAULT_CACHE_BACKEND)
    file_cache.cache_directory = tmp_cache_dir

    # test put: normal
    key = "key"
    value = {"name": "foo"}
    file_cache.put(key, value)
    cache_file = tmp_cache_dir / key
    assert cache_file.exists()

    # test put: permission denied
    with patch("builtins.open", new_callable=mock_open) as fake_open:
        fake_open.side_effect = PermissionError()
        with pytest.raises(JujuSpellError, match="permission denied to write to file"):
            file_cache.put(key, value)

    # test put: general error
    with patch("builtins.open", new_callable=mock_open) as fake_open:
        fake_open.side_effect = Exception()
        with pytest.raises(JujuSpellError):
            file_cache.put(key, value)


def test_03_file_cache_delete(tmp_cache_dir):
    """Test file cache delete method."""
    file_cache = use_cache(DEFAULT_CACHE_BACKEND)
    file_cache.cache_directory = tmp_cache_dir

    # create some data
    key = "key"
    value = {"name": "foo"}
    file_cache.put(key, value)
    cache_file = tmp_cache_dir / key
    assert cache_file.exists()

    # test delete: normal
    file_cache.delete(key)
    assert not cache_file.exists()

    # test delete: not found error
    with pytest.raises(JujuSpellError, match="does not exists."):
        file_cache.delete("non-existing-key")
    # test put: permission denied
    with patch("pathlib.Path.unlink") as mock_unlink:
        mock_unlink.side_effect = PermissionError()
        with pytest.raises(JujuSpellError, match="permission denied to delete file"):
            file_cache.delete(key)

    # test put: general error
    with patch("pathlib.Path.unlink") as mock_unlink:
        mock_unlink.side_effect = Exception()
        with pytest.raises(JujuSpellError):
            print(file_cache.cache_directory)
            file_cache.delete(key)


def test_unknown_backend():
    with pytest.raises(JujuSpellError, match=f"Supported cache backends are {AVALIABLE_BACKENDS}"):
        use_cache("unknown_backend")
