from unittest.mock import AsyncMock, Mock, patch

import pytest

from juju_spell.commands.list_models import ListModelsCommand


@pytest.mark.asyncio
@patch("juju_spell.commands.list_models.use_cache")
async def test_execute_with_refresh(mock_use_cache):
    """Test execute function for ListModelsCommand with --refresh."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    await list_models.execute(
        controller=mock_controller,
        refresh=True,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_controller.list_models.assert_awaited_once()


@pytest.mark.asyncio
@patch("juju_spell.commands.list_models.use_cache")
async def test_10_execute_without_refresh_has_cache(mock_use_cache):
    """Test execute function for ListModelsCommand without --refresh and have existing cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    mock_cache = Mock()
    mock_cache.get.return_value = {"data": {"refresh": False, "models": []}}
    mock_cache.check_expired.return_value = False
    mock_use_cache.return_value = mock_cache

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_controller.list_models.assert_not_awaited()


@pytest.mark.asyncio
@patch("juju_spell.commands.list_models.use_cache")
async def test_11_execute_without_refresh_no_cache(mock_use_cache):
    """Test execute function for ListModelsCommand without --refresh and no existing cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()
    list_models.logger.debug = Mock()

    mock_cache = Mock()
    mock_cache.get.return_value = None
    mock_cache.check_expired.return_value = False
    mock_use_cache.return_value = mock_cache

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_controller.list_models.assert_awaited_once()


@pytest.mark.asyncio
@patch("juju_spell.commands.list_models.use_cache")
async def test_12_execute_without_refresh_expired_cache(mock_use_cache):
    """Test execute function for ListModelsCommand without --refresh and have expired cache."""
    mock_controller = AsyncMock()
    mock_controller_config = Mock()
    list_models = ListModelsCommand()

    mock_cache = Mock()
    mock_cache.get.return_value = {"data": {"refresh": False, "models": []}}
    mock_cache.check_expired.return_value = True
    mock_use_cache.return_value = mock_cache

    await list_models.execute(
        controller=mock_controller,
        refresh=False,
        controller_config=mock_controller_config,
        models=None,
    )

    mock_controller.list_models.assert_awaited_once()
