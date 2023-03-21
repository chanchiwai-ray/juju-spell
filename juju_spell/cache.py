# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2021-2022 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Data structures to offer caching cache to juju-spell."""
from __future__ import annotations

import dataclasses
import logging
from abc import ABCMeta, abstractmethod
from pathlib import Path
from time import time
from typing import Any, Dict, Optional

import yaml

from juju_spell.exceptions import JujuSpellError
from juju_spell.settings import DEFAULT_CACHE_DIR

logger = logging.getLogger(__name__)

DEFAULT_TTL_RULE = 3600  # in seconds
DEFAULT_CACHE_BACKEND = "FileCache"
AVALIABLE_BACKENDS = {DEFAULT_CACHE_BACKEND}


def use_cache(backend: str = DEFAULT_CACHE_BACKEND) -> "Cache":
    """Get the cache class based on the caching backend."""
    if backend not in AVALIABLE_BACKENDS:
        raise JujuSpellError(f"Supported cache backends are {AVALIABLE_BACKENDS}")
    return FileCache()


@dataclasses.dataclass
class CachePolicy:
    """A class for cache policy."""

    ttl: int = DEFAULT_TTL_RULE


class Cache(metaclass=ABCMeta):
    """A cache for command's output with cache policy."""

    policy: CachePolicy = CachePolicy()
    cache_directory: Path = DEFAULT_CACHE_DIR

    def __init__(self) -> None:
        """Initialize the cache."""
        if not self.cache_directory.exists():
            self.cache_directory.mkdir()

    @abstractmethod
    def get(self, key: str) -> Any:
        """Get the data from the cache."""

    @abstractmethod
    def put(self, key: str, value: Any) -> None:
        """Add or update the data in the cache."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete the data from the cache."""


@dataclasses.dataclass
class FileCacheContext:
    """A context for holding output from each command."""

    timestamp: float = time()
    data: Dict[str, Any] = dataclasses.field(default_factory=dict)


class FileCache(Cache):
    """Create a cache file to store the data."""

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get the data from the file cache."""
        context = self._connect(key)
        if not context:
            return None
        if self._check_expired(context):
            self._remove(key)
            return None
        return dataclasses.asdict(context)

    def put(self, key: str, value: Dict[str, Any]) -> None:
        """Add or update the data in the file cache."""
        self._commit(key, FileCacheContext(timestamp=time(), data=value))

    def delete(self, key: str) -> None:
        """Delete the data from the file cache."""
        self._remove(key)

    def _check_expired(self, context: FileCacheContext) -> bool:
        """Check if the cache is expired or not."""
        return context.timestamp + self.policy.ttl < time()

    def _commit(self, key: str, context: FileCacheContext) -> None:
        """Commit the changes to the disk."""
        cache_name = self.cache_directory / key
        try:
            with open(cache_name, "w", encoding="UTF-8") as file:
                data = yaml.safe_dump(dataclasses.asdict(context))
                file.write(data)
        except PermissionError as error:
            raise JujuSpellError(f"permission denied to write to file `{cache_name}`.") from error
        except Exception as error:
            raise JujuSpellError(f"{str(error)}.") from error

    def _connect(self, key: str) -> Optional[FileCacheContext]:
        """Connect to file cache or create a new file cache."""
        cache_name = self.cache_directory / key
        try:
            if not cache_name.exists():
                return None
            with open(cache_name, "r", encoding="UTF-8") as file:
                return FileCacheContext(**yaml.safe_load(file))
        except PermissionError as error:
            raise JujuSpellError(f"permission denied to read from file `{cache_name}`.") from error
        except Exception as error:
            raise JujuSpellError(f"{str(error)}.") from error

    def _remove(self, key: str) -> None:
        """Remove the data from the file cache."""
        cache_name = self.cache_directory / key
        try:
            cache_name.unlink()
        except FileNotFoundError as error:
            raise JujuSpellError(f"`{cache_name}` does not exists.") from error
        except PermissionError as error:
            raise JujuSpellError(f"permission denied to delete file `{cache_name}`.") from error
        except Exception as error:
            raise JujuSpellError(f"{str(error)}.") from error
