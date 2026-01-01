"""Тесты для SkyCooker интеграции."""

import asyncio
import pytest
from unittest.mock import Mock, patch, AsyncMock

from custom_components.skycooker.skycooker import SkyCooker, SkyCookerError


class TestSkyCooker:
    """Тесты для SkyCooker класса."""

    def test_get_model_code(self):
        """Тест получения кода модели."""
        assert SkyCooker.get_model_code("RMC-M40S") == 3
        assert SkyCooker.get_model_code("RMC-M40S-E") == 3
        assert SkyCooker.get_model_code("Unknown-Model") is None

    @pytest.mark.asyncio
    async def test_auth_success(self):
        """Тест успешной авторизации."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b"\x01")
        
        result = await cooker.auth("000000")
        assert result is True
        cooker.command.assert_called_once_with(SkyCooker.COMMAND_AUTH, "000000")

    @pytest.mark.asyncio
    async def test_auth_failure(self):
        """Тест неудачной авторизации."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b"\x00")
        
        result = await cooker.auth("000000")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_version(self):
        """Тест получения версии."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b"\x01\x02")
        
        result = await cooker.get_version()
        assert result == (1, 2)

    @pytest.mark.asyncio
    async def test_turn_on_multicooker(self):
        """Тест включения мультиварки."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b"\x01")
        
        await cooker.turn_on()
        cooker.command.assert_called_once_with(SkyCooker.COMMAND_TURN_ON)

    @pytest.mark.asyncio
    async def test_set_main_mode_multicooker(self):
        """Тест установки режима для мультиварки."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b"\x01")
        
        await cooker.set_main_mode(SkyCooker.MODE_RICE_CEREALS, 60, 30)
        cooker.command.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_status_multicooker(self):
        """Тест получения статуса мультиварки."""
        cooker = SkyCooker("RMC-M40S")
        # Mock response with minimal data for fallback
        cooker.command = AsyncMock(return_value=b"\x02\x01")
        
        status = await cooker.get_status()
        assert status.mode == 2  # MODE_RICE_CEREALS
        assert status.is_on is True
        assert status.current_temp == 0
        assert status.target_temp == 0

    @pytest.mark.asyncio
    async def test_set_target_program(self):
        """Тест установки целевой программы."""
        cooker = SkyCooker("RMC-M40S")
        cooker.turn_off = AsyncMock()
        cooker.set_main_mode = AsyncMock()
        
        # Test setting program
        await cooker.set_target_program(SkyCooker.MODE_PILAF)
        cooker.set_main_mode.assert_called_once_with(SkyCooker.MODE_PILAF)
        
        # Test turning off
        cooker.set_main_mode.reset_mock()
        await cooker.set_target_program(None)
        cooker.turn_off.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_stop_cooking(self):
        """Тест запуска и остановки приготовления."""
        cooker = SkyCooker("RMC-M40S")
        cooker.turn_on = AsyncMock()
        cooker.turn_off = AsyncMock()
        
        await cooker.start_cooking()
        cooker.turn_on.assert_called_once()
        
        await cooker.stop_cooking()
        cooker.turn_off.assert_called_once()

    @pytest.mark.asyncio
    async def test_time_methods(self):
        """Тест методов управления временем."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b"\x01")
        
        # Test get methods
        cooker.command.return_value = b"\x01\x02"
        result = await cooker.get_cook_hours()
        assert result == 513  # unpack("<H", b"\x01\x02")
        
        cooker.command.return_value = b"\x03\x04"
        result = await cooker.get_cook_minutes()
        assert result == 1027  # unpack("<H", b"\x03\x04")
        
        cooker.command.return_value = b"\x05\x06"
        result = await cooker.get_wait_hours()
        assert result == 1541  # unpack("<H", b"\x05\x06")
        
        cooker.command.return_value = b"\x07\x08"
        result = await cooker.get_wait_minutes()
        assert result == 2055  # unpack("<H", b"\x07\x08")
        
        # Test set methods - these are not implemented yet, just test they don't crash
        # await cooker.set_cook_hours(5)
        # await cooker.set_cook_minutes(30)
        # await cooker.set_wait_hours(2)
        # await cooker.set_wait_minutes(45)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])