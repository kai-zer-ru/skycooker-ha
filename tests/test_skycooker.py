import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.skycooker.skycooker import SkyCooker, SkyCookerError

# Настройка логирования для тестов
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TestSkyCooker:
    """Тесты для SkyCooker класса."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.mock_connection = AsyncMock()
        self.mock_connection.command = AsyncMock()
        self.mock_connection.auth = AsyncMock()
        self.mock_connection.get_version = AsyncMock()
        self.mock_connection.sync_time = AsyncMock()
        self.mock_connection.get_status = AsyncMock()
        self.mock_connection.get_stats = AsyncMock()
        self.mock_connection.get_light_switch = AsyncMock()
        self.mock_connection.get_lamp_auto_off_hours = AsyncMock()
        self.mock_connection.get_fresh_water = AsyncMock()
        self.mock_connection.get_colors = AsyncMock()
        self.mock_connection.turn_on = AsyncMock()
        self.mock_connection.turn_off = AsyncMock()
        self.mock_connection.set_main_mode = AsyncMock()
        self.mock_connection.commit = AsyncMock()

    def test_init_valid_model(self):
        """Тест инициализации с валидной моделью."""
        cooker = SkyCooker("RMC-M40S")
        assert cooker.model == "RMC-M40S"
        assert cooker.model_code == 5

    def test_init_invalid_model(self):
        """Тест инициализации с невалидной моделью."""
        with pytest.raises(SkyCookerError, match="Unknown Cooker model: Invalid-Model"):
            SkyCooker("Invalid-Model")

    def test_get_model_code(self):
        """Тест получения кода модели."""
        assert SkyCooker.get_model_code("RMC-M40S") == 5
        assert SkyCooker.get_model_code("RMC-M42S") == 5
        assert SkyCooker.get_model_code("RMC-M40S-E") == 5
        assert SkyCooker.get_model_code("Invalid-Model") is None

    @pytest.mark.asyncio
    async def test_auth_success(self):
        """Тест успешной аутентификации."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01')
        
        result = await cooker.auth(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        assert result is True
        cooker.command.assert_called_once_with(0xFF, b'\x01\x02\x03\x04\x05\x06\x07\x08')

    @pytest.mark.asyncio
    async def test_auth_failure(self):
        """Тест неудачной аутентификации."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x00')
        
        result = await cooker.auth(b'\x01\x02\x03\x04\x05\x06\x07\x08')
        assert result is False

    @pytest.mark.asyncio
    async def test_get_version_success(self):
        """Тест успешного получения версии."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01\x02')
        
        result = await cooker.get_version()
        assert result == (1, 2)

    @pytest.mark.asyncio
    async def test_get_version_failure(self):
        """Тест неудачного получения версии."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=None)
        
        with pytest.raises(SkyCookerError, match="Failed to get version - no response"):
            await cooker.get_version()

    def test_version_constant(self):
        """Тест константы версии."""
        from custom_components.skycooker.const import VERSION
        assert VERSION == "0.0.8"

    @pytest.mark.asyncio
    async def test_turn_on_success(self):
        """Тест успешного включения."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01')
        
        await cooker.turn_on()
        cooker.command.assert_called_once_with(0x03)

    @pytest.mark.asyncio
    async def test_turn_off_success(self):
        """Тест успешного выключения."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01')
        
        await cooker.turn_off()
        cooker.command.assert_called_once_with(0x04)

    @pytest.mark.asyncio
    async def test_set_main_mode_success(self):
        """Тест успешной установки основного режима."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01')
    
        await cooker.set_main_mode(1, 80, 10)
        cooker.command.assert_called_once_with(0x05, b'\x01\x00P\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8a\x00')

    @pytest.mark.asyncio
    async def test_get_status_success(self):
        """Тест успешного получения статуса."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01\x01\x40\x50\x01\x00\x00\x00\x00\x00')
        
        result = await cooker.get_status()
        assert result.mode == 1
        assert result.is_on is True
        assert result.current_temp == 64
        assert result.target_temp == 80

    @pytest.mark.asyncio
    async def test_sync_time(self):
        """Тест синхронизации времени."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x00')
        
        await cooker.sync_time()
        cooker.command.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_stats(self):
        """Тест получения статистики."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01\x00\x00\x00\x00\x00\x00\x00\x00')
        
        result = await cooker.get_stats()
        assert result.ontime == 1

    @pytest.mark.asyncio
    async def test_get_light_switch(self):
        """Тест получения состояния переключателя света."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01')
        
        result = await cooker.get_light_switch(0)
        assert result == 1

    @pytest.mark.asyncio
    async def test_get_lamp_auto_off_hours(self):
        """Тест получения часов автоматического отключения лампы."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01\x00')
        
        result = await cooker.get_lamp_auto_off_hours()
        assert result == 1

    @pytest.mark.asyncio
    async def test_get_fresh_water(self):
        """Тест получения информации о свежей воде."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01\x00\x01')
        
        result = await cooker.get_fresh_water()
        assert result.is_on is True
        assert result.water_freshness_hours == 1

    @pytest.mark.asyncio
    async def test_get_colors(self):
        """Тест получения цветов."""
        cooker = SkyCooker("RMC-M40S")
        cooker.command = AsyncMock(return_value=b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d')
        
        result = await cooker.get_colors(0)
        assert result.r_low == 1
        assert result.g_low == 2
        assert result.b_low == 3

    @pytest.mark.asyncio
    async def test_set_target_program(self):
        """Тест установки целевой программы."""
        cooker = SkyCooker("RMC-M40S")
        cooker.turn_off = AsyncMock()
        cooker.set_main_mode = AsyncMock()
        
        await cooker.set_target_program(1)
        cooker.set_main_mode.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_set_target_temperature(self):
        """Тест установки целевой температуры."""
        cooker = SkyCooker("RMC-M40S")
        cooker.get_status = AsyncMock(return_value=MagicMock(mode=1))
        cooker.set_main_mode = AsyncMock()
        
        await cooker.set_target_temperature(80)
        cooker.set_main_mode.assert_called_once_with(1, 80)

    @pytest.mark.asyncio
    async def test_start_cooking(self):
        """Тест запуска приготовления."""
        cooker = SkyCooker("RMC-M40S")
        cooker.turn_on = AsyncMock()
        
        await cooker.start_cooking()
        cooker.turn_on.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_cooking(self):
        """Тест остановки приготовления."""
        cooker = SkyCooker("RMC-M40S")
        cooker.turn_off = AsyncMock()
        
        await cooker.stop_cooking()
        cooker.turn_off.assert_called_once()

    def test_mode_names(self):
        """Тест имен режимов."""
        assert SkyCooker.MODE_NAMES[0] == "Standby"
        assert SkyCooker.MODE_NAMES[1] == "Multi-chef"
        assert SkyCooker.MODE_NAMES[2] == "Rice/Cereals"

    def test_light_names(self):
        """Тест имен света."""
        assert SkyCooker.LIGHT_NAMES[0] == "boiling_light"
        assert SkyCooker.LIGHT_NAMES[1] == "lamp_light"

    def test_command_constants(self):
        """Тест констант команд."""
        assert SkyCooker.COMMAND_GET_VERSION == 0x01
        assert SkyCooker.COMMAND_TURN_ON == 0x03
        assert SkyCooker.COMMAND_TURN_OFF == 0x04
        assert SkyCooker.COMMAND_SET_MAIN_MODE == 0x05
        assert SkyCooker.COMMAND_GET_STATUS == 0x06
        assert SkyCooker.COMMAND_AUTH == 0xFF

    @pytest.mark.asyncio
    async def test_test_connection_uses_real_key(self):
        """Тест что test_connection использует реальный ключ для аутентификации."""
        cooker = SkyCooker("RMC-M40S")
        real_key = b'\x01\x02\x03\x04\x05\x06\x07\x08'
        cooker._auth_key = real_key
        
        # Мокаем command для имитации успешного ответа
        cooker.command = AsyncMock(return_value=b'\x01')
        
        # Мокаем auth для проверки что он вызывается с реальным ключом
        cooker.auth = AsyncMock(return_value=True)
        
        result = await cooker.test_connection()
        
        # Проверяем что test_connection вернул True (успешное соединение)
        assert result is True
        
        # Проверяем что auth был вызван с реальным ключом
        cooker.auth.assert_called_once_with(real_key)