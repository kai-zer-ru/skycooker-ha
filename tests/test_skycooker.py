# Тесты для модуля skycooker.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from custom_components.skycooker.skycooker import SkyCooker, SkyCookerError
from custom_components.skycooker.const import MODEL_3, MODEL_6


class SkyCookerTestImpl(SkyCooker):
    """Конкретная реализация SkyCooker для тестирования."""
    
    def __init__(self, hass, model_name):
        super().__init__(hass, model_name)
        self.command_calls = []
    
    async def command(self, command: int, params=None):
        """Реализация абстрактного метода command."""
        self.command_calls.append((command, params))
        # Возвращаем успешный ответ по умолчанию
        return bytes([1])


def test_skycooker_initialization():
    """Тест инициализации SkyCooker."""
    mock_hass = MagicMock()
    
    # Тест успешной инициализации
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    assert skycooker is not None
    assert skycooker.hass == mock_hass
    assert skycooker.model_name == "RMC-M40S"
    assert skycooker.model_id == MODEL_3
    
    # Тест с неизвестной моделью (покрытие строки 66: raise SkyCookerError)
    with pytest.raises(SkyCookerError, match="Unknown SkyCooker model"):
        SkyCookerTestImpl(mock_hass, "UNKNOWN_MODEL")


def test_get_model_id():
    """Тест получения кода модели."""
    # Тест с известной моделью
    model_id = SkyCooker.get_model_id("RMC-M40S")
    assert model_id == MODEL_3
    
    # Тест с моделью, оканчивающейся на -E
    model_id = SkyCooker.get_model_id("RMC-M40S-E")
    assert model_id == MODEL_3
    
    # Тест с неизвестной моделью
    model_id = SkyCooker.get_model_id("UNKNOWN_MODEL")
    assert model_id is None


@pytest.mark.asyncio
async def test_auth_success():
    """Тест успешной аутентификации."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды
    skycooker.command = AsyncMock(return_value=bytes([1]))
    
    result = await skycooker.auth(b"test_key")
    assert result is True
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_auth_failure():
    """Тест неудачной аутентификации."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды с ошибкой
    skycooker.command = AsyncMock(return_value=bytes([0]))
    
    result = await skycooker.auth(b"test_key")
    assert result is False
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_get_version():
    """Тест получения версии."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды
    skycooker.command = AsyncMock(return_value=bytes([1, 2]))
    
    version = await skycooker.get_version()
    assert version == "1.2"
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_turn_on_success():
    """Тест успешного включения."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды
    skycooker.command = AsyncMock(return_value=bytes([1]))
    
    await skycooker.turn_on()
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_turn_on_failure():
    """Тест неудачного включения."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды с ошибкой
    skycooker.command = AsyncMock(return_value=bytes([0]))
    
    with pytest.raises(SkyCookerError):
        await skycooker.turn_on()


@pytest.mark.asyncio
async def test_turn_off_success():
    """Тест успешного выключения."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды
    skycooker.command = AsyncMock(return_value=bytes([1]))
    
    await skycooker.turn_off()
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_turn_off_failure():
    """Тест неудачного выключения."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды с ошибкой
    skycooker.command = AsyncMock(return_value=bytes([0]))
    
    with pytest.raises(SkyCookerError):
        await skycooker.turn_off()


@pytest.mark.asyncio
async def test_select_program_success():
    """Тест успешного выбора программы."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды
    skycooker.command = AsyncMock(return_value=bytes([1]))
    
    await skycooker.select_program(1, 0)
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_select_program_failure():
    """Тест неудачного выбора программы."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды с ошибкой (код ошибки 2, длина 1)
    skycooker.command = AsyncMock(return_value=bytes([2]))
    
    # Проверяем, что метод не выбрасывает исключение при ошибке
    await skycooker.select_program(1, 0)
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_set_main_program_success():
    """Тест успешной установки основной программы."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды
    skycooker.command = AsyncMock(return_value=bytes([1]))
    
    await skycooker.set_main_program(
        program_id=1,
        subprogram_id=0,
        target_temperature=100,
        target_main_hours=1,
        target_main_minutes=30,
        target_additional_hours=0,
        target_additional_minutes=0,
        auto_warm=1,
        bit_flags=0
    )
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_set_main_program_failure():
    """Тест неудачной установки основной программы."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    
    # Мокаем ответ команды с ошибкой (код ошибки 2, длина 1)
    skycooker.command = AsyncMock(return_value=bytes([2]))
    
    # Проверяем, что метод не выбрасывает исключение при ошибке
    await skycooker.set_main_program(
        program_id=1,
        subprogram_id=0,
        target_temperature=100,
        target_main_hours=1,
        target_main_minutes=30,
        target_additional_hours=0,
        target_additional_minutes=0,
        auto_warm=1,
        bit_flags=0
    )
    skycooker.command.assert_called_once()


@pytest.mark.asyncio
async def test_command_abstract():
    """Тест абстрактного метода command."""
    mock_hass = MagicMock()

    # Проверяем, что метод command является абстрактным
    with pytest.raises(TypeError):
        SkyCooker(mock_hass, "RMC-M40S")


@pytest.mark.asyncio
async def test_select_program_model_with_subprograms():
    """Тест select_program для модели с поддержкой подпрограмм (RMC-M92S)."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M92S")
    assert skycooker.model_id == MODEL_6

    skycooker.command = AsyncMock(return_value=bytes([1]))
    await skycooker.select_program(1, 2)
    skycooker.command.assert_called_once()
    # Проверяем, что переданы 2 байта (program_id, subprog)
    call_args = skycooker.command.call_args[0]
    assert call_args[0] == 0x09  # COMMAND_SELECT_PROGRAM
    assert len(call_args[1]) == 2


@pytest.mark.asyncio
async def test_select_program_error_response():
    """Тест select_program при ответе с кодом ошибки (r[0]!=1, len>1)."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    skycooker.command = AsyncMock(return_value=bytes([2, 0]))

    with pytest.raises(SkyCookerError, match="Ошибка выбора режима"):
        await skycooker.select_program(1, 0)


@pytest.mark.asyncio
async def test_select_program_command_exception():
    """Тест select_program при исключении в command."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    skycooker.command = AsyncMock(side_effect=ConnectionError("Connection failed"))

    with pytest.raises(SkyCookerError, match="Исключение при выборе режима"):
        await skycooker.select_program(1, 0)


@pytest.mark.asyncio
async def test_set_main_program_model_with_subprograms():
    """Тест set_main_program для модели с поддержкой подпрограмм."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M92S")

    skycooker.command = AsyncMock(return_value=bytes([1]))
    await skycooker.set_main_program(
        program_id=1,
        subprogram_id=2,
        target_temperature=100,
        target_main_hours=1,
        target_main_minutes=30,
    )
    call_args = skycooker.command.call_args[0]
    assert len(call_args[1]) == 9  # BBBBBBBBB для модели с подпрограммами


@pytest.mark.asyncio
async def test_set_main_program_model3_no_subprogram():
    """Тест set_main_program для MODEL_3 (без подпрограмм) — 8 байт."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")

    skycooker.command = AsyncMock(return_value=bytes([1]))
    await skycooker.set_main_program(
        program_id=1,
        subprogram_id=99,  # Игнорируется для MODEL_3
        target_temperature=100,
        target_main_hours=1,
        target_main_minutes=30,
    )
    call_args = skycooker.command.call_args[0]
    assert len(call_args[1]) == 8  # BBBBBBBB для MODEL_3


@pytest.mark.asyncio
async def test_set_main_program_error_response():
    """Тест set_main_program при ответе с кодом ошибки."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    skycooker.command = AsyncMock(return_value=bytes([3, 0]))

    with pytest.raises(SkyCookerError, match="Ошибка установки режима"):
        await skycooker.set_main_program(
            program_id=1,
            target_temperature=100,
        )


@pytest.mark.asyncio
async def test_set_main_program_command_exception():
    """Тест set_main_program при исключении в command."""
    mock_hass = MagicMock()
    skycooker = SkyCookerTestImpl(mock_hass, "RMC-M40S")
    skycooker.command = AsyncMock(side_effect=TimeoutError("Timeout"))

    with pytest.raises(SkyCookerError, match="Исключение при установке режима"):
        await skycooker.set_main_program(
            program_id=1,
            target_temperature=100,
        )