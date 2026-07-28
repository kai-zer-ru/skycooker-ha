# Тесты для модуля skycooker_state_manager.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker_state_manager import SkyCookerStateManager, SkyCookerError
from custom_components.skycooker.const import STATUS_OFF


def test_state_manager_initialization():
    """Тест инициализации менеджера состояния."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    assert state_manager is not None
    assert state_manager.connection_manager == mock_connection_manager
    assert state_manager.cooking_controller == mock_cooking_controller
    assert state_manager._stats is None


@pytest.mark.asyncio
async def test_update_success():
    """Тест успешного обновления состояния."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = False
    mock_connection_manager.available = True
    mock_connection_manager.update_lock = AsyncMock()
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.get_status = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()
    mock_connection_manager.add_stat = MagicMock()
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    # Мокаем статус
    mock_status = MagicMock()
    mock_connection_manager.get_status.return_value = mock_status
    
    result = await state_manager.update()
    
    assert result is True
    mock_connection_manager.connect_if_need.assert_called_once()
    mock_connection_manager.get_status.assert_called_once()
    mock_cooking_controller.status = mock_status
    mock_connection_manager.disconnect_if_need.assert_called_once()
    mock_connection_manager.add_stat.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_update_disposed():
    """Тест обновления состояния при disposed состоянии."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = True
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    result = await state_manager.update()
    
    assert result is None


@pytest.mark.asyncio
async def test_update_failure():
    """Тест неудачного обновления состояния."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = False
    mock_connection_manager.available = True
    mock_connection_manager.update_lock = AsyncMock()
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.get_status = AsyncMock(side_effect=Exception("Test error"))
    mock_connection_manager.disconnect = AsyncMock()
    mock_connection_manager.add_stat = MagicMock()
    mock_cooking_controller.target_program_name = None
    mock_cooking_controller.last_set_target = 0
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    result = await state_manager.update()
    
    assert result is False
    assert mock_connection_manager.connect_if_need.call_count == 3
    assert mock_connection_manager.get_status.call_count == 3
    mock_cooking_controller.status = None
    assert mock_connection_manager.disconnect.call_count == 3
    assert mock_connection_manager.add_stat.call_count == 3


@pytest.mark.asyncio
async def test_commit():
    """Тест применения изменений."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = False
    mock_connection_manager.available = True
    mock_connection_manager.update_lock = AsyncMock()
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.get_status = AsyncMock()
    mock_connection_manager.disconnect_if_need = AsyncMock()
    mock_connection_manager.add_stat = MagicMock()
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    # Мокаем статус
    mock_status = MagicMock()
    mock_connection_manager.get_status.return_value = mock_status
    
    await state_manager.commit()
    
    mock_connection_manager.connect_if_need.assert_called_once()
    mock_connection_manager.get_status.assert_called_once()
    mock_cooking_controller.status = mock_status
    mock_connection_manager.disconnect_if_need.assert_called_once()
    mock_connection_manager.add_stat.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_update_retry():
    """Тест повторного обновления состояния."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = False
    mock_connection_manager.available = True
    mock_connection_manager.update_lock = AsyncMock()
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.get_status = AsyncMock(side_effect=Exception("Test error"))
    mock_connection_manager.disconnect = AsyncMock()
    mock_connection_manager.add_stat = MagicMock()
    mock_cooking_controller.target_program_name = None
    mock_cooking_controller.last_set_target = 0
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    # Мокаем задержку
    import asyncio
    async def mock_sleep(delay):
        pass
    
    with patch('custom_components.skycooker.skycooker_state_manager.asyncio.sleep', side_effect=mock_sleep):
        result = await state_manager.update(tries=2)
    
    assert result is False
    assert mock_connection_manager.get_status.call_count == 2
    mock_connection_manager.disconnect.assert_called()
    assert mock_connection_manager.add_stat.call_count == 2


@pytest.mark.asyncio
async def test_update_auth_error():
    """Тест обновления состояния с ошибкой аутентификации."""
    from custom_components.skycooker.skycooker_connection_manager import AuthError
    
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = False
    mock_connection_manager.available = True
    mock_connection_manager.update_lock = AsyncMock()
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.get_status = AsyncMock(side_effect=AuthError("Auth error"))
    mock_connection_manager.disconnect = AsyncMock()
    mock_connection_manager.add_stat = MagicMock()
    mock_cooking_controller.target_program_name = None
    mock_cooking_controller.last_set_target = 0
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    result = await state_manager.update()
    
    assert result is None
    mock_connection_manager.connect_if_need.assert_called_once()
    mock_connection_manager.get_status.assert_called_once()
    mock_cooking_controller.status = None
    mock_connection_manager.disconnect.assert_called_once()


def test_status_code_property():
    """Тест свойства status_code."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_cooking_controller.status = None
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    # Тест без статуса
    assert state_manager.status_code is None
    
    # Тест со статусом выключено
    mock_status = MagicMock()
    mock_status.is_on = False
    mock_cooking_controller.status = mock_status
    assert state_manager.status_code == STATUS_OFF
    
    # Тест со статусом включено
    mock_status.is_on = True
    mock_status.status = 5
    assert state_manager.status_code == 5


def test_auto_warm_property():
    """Тест свойства auto_warm."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_cooking_controller.status = None
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    # Тест без статуса
    assert state_manager.auto_warm is None
    
    # Тест со статусом
    mock_status = MagicMock()
    mock_status.auto_warm = True
    mock_cooking_controller.status = mock_status
    assert state_manager.auto_warm is True


def test_subprog_property():
    """Тест свойства subprog."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_cooking_controller.status = None
    
    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)
    
    # Тест без статуса
    assert state_manager.subprog is None
    
    # Тест со статусом
    mock_status = MagicMock()
    mock_status.subprogram_id = 1
    mock_cooking_controller.status = mock_status
    assert state_manager.subprog == 1


def test_success_rate_property():
    """Тест свойства success_rate."""
    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.success_rate = 75

    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)

    assert state_manager.success_rate == 75


@pytest.mark.asyncio
async def test_update_failure_reset_target_program_name():
    """Тест сброса target_program_name при таймауте."""
    from custom_components.skycooker.const import TARGET_TTL

    mock_connection_manager = MagicMock()
    mock_cooking_controller = MagicMock()
    mock_connection_manager.disposed = False
    mock_connection_manager.available = True
    mock_connection_manager.update_lock = AsyncMock()
    mock_connection_manager.connect_if_need = AsyncMock()
    mock_connection_manager.get_status = AsyncMock(side_effect=Exception("Test error"))
    mock_connection_manager.disconnect = AsyncMock()
    mock_connection_manager.add_stat = MagicMock()
    mock_cooking_controller.target_program_name = "Суп"
    mock_cooking_controller.last_set_target = 0

    state_manager = SkyCookerStateManager(mock_connection_manager, mock_cooking_controller)

    async def mock_sleep(x):
        pass

    with patch('custom_components.skycooker.skycooker_state_manager.monotonic', return_value=TARGET_TTL + 1):
        with patch('custom_components.skycooker.skycooker_state_manager.asyncio.sleep', side_effect=mock_sleep):
            result = await state_manager.update(tries=1)

    assert result is False
    assert mock_cooking_controller.target_program_name is None