#!/usr/bin/env python3
# coding: utf-8

"""
Основной скрипт для запуска функций библиотеки SkyCooker.
Запуск осуществляется с параметром, указывающим функцию для выполнения.
"""

import asyncio
import argparse
import logging
import sys
import os

# Добавляем путь к библиотеке
sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from lib import SkyCookerLibrary
from lib.skycooker import SkyCooker

_LOGGER = logging.getLogger(__name__)


def parse_status_from_string(status_string):
    """
    Парсинг статуса из строки.
    
    Args:
        status_string (str): Строка статуса в hex-формате.
    
    Returns:
        dict: Разобранные данные статуса.
    """
    try:
        # Настраиваем логгер
        import logging
        logging.basicConfig(level=logging.INFO)
        
        # Обрезаем строку статуса, чтобы оставить только данные статуса
        # Убираем первые 2 байта (заголовок) и последний байт (контрольная сумма)
        if len(status_string) > 6:
            status_string = status_string[6:-2]
        
        # Преобразуем hex-строку в байты
        status_bytes = bytes.fromhex(status_string)
        
        # Используем метод парсинга из библиотеки SkyCooker
        # Создаем временный объект для парсинга
        class TempSkyCooker(SkyCooker):
            async def command(self, command, params=None):
                return status_bytes
        
        temp_skycooker = TempSkyCooker(model="RMC-M40S")
        
        # Эмулируем вызов get_status
        mode = status_bytes[0]
        subprog = status_bytes[1]
        target_temp = status_bytes[2]
        hours = status_bytes[3]
        minutes = status_bytes[4]
        remaining_hours = status_bytes[5]
        remaining_minutes = status_bytes[6]
        auto_warm = status_bytes[7]
        status = status_bytes[8]
        
        result = {
            'mode': mode,
            'subprog': subprog,
            'target_temp': target_temp,
            'hours': hours,
            'minutes': minutes,
            'remaining_hours': remaining_hours,
            'remaining_minutes': remaining_minutes,
            'auto_warm': auto_warm,
            'status': status
        }
        
        # Выводим человеческий текст в логи
        from lib.const import MODE_NAMES, STATUS_CODES, MODEL_3
        
        mode_names = MODE_NAMES[MODEL_3][1]
        status_codes = STATUS_CODES[1]
        
        mode_name = mode_names[mode] if mode < len(mode_names) else f"Неизвестный режим ({mode})"
        status_name = status_codes.get(status, f"Неизвестный статус ({status})")
        
        _LOGGER.info(f"📊 Разобранный статус:")
        _LOGGER.info(f"  Режим: {mode_name} {mode}")
        _LOGGER.info(f"  Подрежим: {subprog}")
        _LOGGER.info(f"  Целевая температура: {target_temp}°C")
        _LOGGER.info(f"  Время: {hours} часов {minutes} минут")
        _LOGGER.info(f"  Оставшееся время: {remaining_hours} часов {remaining_minutes} минут")
        _LOGGER.info(f"  Автоподогрев: {'Включен' if auto_warm else 'Выключен'}")
        _LOGGER.info(f"  Статус: {status_name} - {status}")
        
        return result
    except Exception as e:
        _LOGGER.error(f"❌ Ошибка при разборе строки статуса: {e}")
        return None


async def check_connection(library, mac, key):
    """
    Проверка подключения к мультиварке.
    """
    _LOGGER.info("🔌 Проверка подключения к мультиварке...")
    result = await library.check_connection()
    if result:
        _LOGGER.info("✅ Подключение успешно")
    else:
        _LOGGER.error("❌ Подключение не удалось")
    return result


async def sync_time(library, mac, key):
    """
    Синхронизация времени с мультиваркой.
    """
    _LOGGER.info("🕒 Синхронизация времени с мультиваркой...")
    result = await library.sync_time()
    if result:
        _LOGGER.info("✅ Время синхронизировано")
    else:
        _LOGGER.error("❌ Синхронизация времени не удалась")
    return result


async def get_time(library, mac, key):
    """
    Получение времени от мультиварки.
    """
    _LOGGER.info("⏰ Получение времени от мультиварки...")
    result = await library.get_time()
    if result:
        t, offset = result
        _LOGGER.info(f"⏰ Время мультиварки: {t}, смещение: {offset}")
    else:
        _LOGGER.error("❌ Получение времени не удалось")
    return result


async def get_version(library, mac, key):
    """
    Получение версии от мультиварки.
    """
    _LOGGER.info("📋 Получение версии от мультиварки...")
    result = await library.get_version()
    if result:
        _LOGGER.info(f"📋 Версия мультиварки: {result}")
    else:
        _LOGGER.error("❌ Получение версии не удалось")
    return result


async def get_status(library, mac, key, continuous=False):
    """
    Получение статуса от мультиварки.
    
    Args:
        continuous (bool): Если True, получать статус в бесконечном цикле.
    """
    _LOGGER.info("📊 Получение статуса от мультиварки...")
    if continuous:
        _LOGGER.info("🔄 Получение статуса в бесконечном цикле (Ctrl+C для остановки)...")
        try:
            while True:
                result = await library.get_status()
                if result:
                    _LOGGER.info(f"📊 Статус мультиварки: {result}")
                else:
                    _LOGGER.error("❌ Получение статуса не удалось")
                await asyncio.sleep(5)
        except KeyboardInterrupt:
            _LOGGER.info("🛑 Остановка непрерывного получения статуса...")
    else:
        result = await library.get_status()
        if result:
            _LOGGER.info(f"📊 Статус мультиварки: {result}")
        else:
            _LOGGER.error("❌ Получение статуса не удалось")
        return result


async def turn_on(library, mac, key):
    """
    Включение мультиварки.
    """
    _LOGGER.info("🔌 Включение мультиварки...")
    result = await library.turn_on()
    if result:
        _LOGGER.info("✅ Мультиварка включена")
    else:
        _LOGGER.error("❌ Включение мультиварки не удалось")
    return result


async def turn_off(library, mac, key):
    """
    Выключение мультиварки.
    """
    _LOGGER.info("🔌 Выключение мультиварки...")
    result = await library.turn_off()
    if result:
        _LOGGER.info("✅ Мультиварка выключена")
    else:
        _LOGGER.error("❌ Выключение мультиварки не удалось")
    return result


async def set_mode(library, mac, key, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0):
    """
    Выбор и запуск режима.
    
    Args:
        mode (int): Режим работы мультиварки.
        subprog (int): Подрежим.
        target_temp (int): Целевая температура.
        hours (int): Часы.
        minutes (int): Минуты.
        dhours (int): Часы задержки.
        dminutes (int): Минуты задержки.
        heat (int): Нагрев.
    """
    _LOGGER.info(f"🔧 Установка режима {mode}...")
    result = await library.set_mode(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
    if result:
        _LOGGER.info(f"✅ Режим {mode} установлен")
    else:
        _LOGGER.error("❌ Установка режима не удалась")
    return result


async def set_mode_default(library, mac, key, mode):
    """
    Выбор и запуск режима с параметрами по умолчанию.
    
    Args:
        mode (int): Режим работы мультиварки.
    """
    _LOGGER.info(f"🔧 Установка режима {mode} с параметрами по умолчанию...")
    result = await library.set_mode_default(mode)
    if result:
        _LOGGER.info(f"✅ Режим {mode} установлен с параметрами по умолчанию")
    else:
        _LOGGER.error("❌ Установка режима с параметрами по умолчанию не удалась")
    return result


async def set_delayed_mode(library, mac, key, mode, subprog=0, target_temp=0, hours=0, minutes=0, dhours=0, dminutes=0, heat=0):
    """
    Выбор и запуск режима с отложенным временем.
    
    Args:
        mode (int): Режим работы мультиварки.
        subprog (int): Подрежим.
        target_temp (int): Целевая температура.
        hours (int): Часы.
        minutes (int): Минуты.
        dhours (int): Часы задержки.
        dminutes (int): Минуты задержки.
        heat (int): Нагрев.
    """
    _LOGGER.info(f"🔧 Установка режима {mode} с отложенным временем...")
    result = await library.set_delayed_mode(mode, subprog, target_temp, hours, minutes, dhours, dminutes, heat)
    if result:
        _LOGGER.info(f"✅ Режим {mode} с отложенным временем установлен")
    else:
        _LOGGER.error("❌ Установка режима с отложенным временем не удалась")
    return result


async def main():
    """
    Основная функция для запуска скрипта.
    """
    parser = argparse.ArgumentParser(description='Управление мультиваркой SkyCooker')
    parser.add_argument('function', type=str, help='Функция для выполнения')
    parser.add_argument('--mac', type=str, default='DA:D8:9F:9E:0B:4C', help='MAC-адрес мультиварки')
    parser.add_argument('--key', type=str, default='0000000000000000', help='Ключ аутентификации')
    parser.add_argument('--model', type=str, default='RMC-M40S', help='Модель мультиварки')
    parser.add_argument('--mode', type=int, help='Режим работы мультиварки')
    parser.add_argument('--target_temp', type=int, default=0, help='Целевая температура')
    parser.add_argument('--boil_time', type=int, default=0, help='Время кипения')
    parser.add_argument('--subprog', type=int, default=0, help='Подрежим')
    parser.add_argument('--hours', type=int, default=0, help='Часы')
    parser.add_argument('--minutes', type=int, default=0, help='Минуты')
    parser.add_argument('--dhours', type=int, default=0, help='Часы задержки')
    parser.add_argument('--dminutes', type=int, default=0, help='Минуты задержки')
    parser.add_argument('--heat', type=int, default=0, help='Нагрев')
    parser.add_argument('--wait_hours', type=int, default=0, help='Часы до начала')
    parser.add_argument('--wait_minutes', type=int, default=0, help='Минуты до начала')
    parser.add_argument('--continuous', action='store_true', help='Получать статус в бесконечном цикле')
    parser.add_argument('--status_string', type=str, help='Строка статуса для парсинга')
    
    args = parser.parse_args()
    
    if args.function == 'parse_status_string':
        if args.status_string:
            parsed_status = parse_status_from_string(args.status_string)
            if parsed_status:
                print(parsed_status)
            else:
                print("❌ Не удалось разобрать строку статуса")
        else:
            _LOGGER.error("❌ Не указана строка статуса (--status_string)")
        return
    
    library = SkyCookerLibrary(mac=args.mac, key=args.key, model=args.model)
    
    try:
        if args.function == 'check_connection':
            await check_connection(library, args.mac, args.key)
        elif args.function == 'sync_time':
            await sync_time(library, args.mac, args.key)
        elif args.function == 'get_time':
            await get_time(library, args.mac, args.key)
        elif args.function == 'get_version':
            await get_version(library, args.mac, args.key)
        elif args.function == 'get_status':
            await get_status(library, args.mac, args.key, args.continuous)
        elif args.function == 'turn_on':
            await turn_on(library, args.mac, args.key)
        elif args.function == 'turn_off':
            await turn_off(library, args.mac, args.key)
        elif args.function == 'set_mode':
            if args.mode is None:
                _LOGGER.error("❌ Не указан режим (--mode)")
                return
            await set_mode(library, args.mac, args.key, args.mode, args.subprog, args.target_temp, args.hours, args.minutes, args.dhours, args.dminutes, args.heat)
        elif args.function == 'set_mode_default':
            if args.mode is None:
                _LOGGER.error("❌ Не указан режим (--mode)")
                return
            await set_mode_default(library, args.mac, args.key, args.mode)
        elif args.function == 'set_delayed_mode':
            if args.mode is None:
                _LOGGER.error("❌ Не указан режим (--mode)")
                return
            await set_delayed_mode(library, args.mac, args.key, args.mode, args.subprog, args.target_temp, args.hours, args.minutes, args.dhours, args.dminutes, args.heat)
        else:
            _LOGGER.error(f"❌ Неизвестная функция: {args.function}")
            _LOGGER.info("📋 Доступные функции:")
            _LOGGER.info("  - check_connection: Проверка подключения к мультиварке")
            _LOGGER.info("  - sync_time: Синхронизация времени с мультиваркой")
            _LOGGER.info("  - get_time: Получение времени от мультиварки")
            _LOGGER.info("  - get_version: Получение версии от мультиварки")
            _LOGGER.info("  - get_status: Получение статуса от мультиварки")
            _LOGGER.info("  - turn_on: Включение мультиварки")
            _LOGGER.info("  - turn_off: Выключение мультиварки")
            _LOGGER.info("  - set_mode: Выбор и запуск режима")
            _LOGGER.info("  - set_mode_default: Выбор и запуск режима с параметрами по умолчанию")
            _LOGGER.info("  - set_delayed_mode: Выбор и запуск режима с отложенным временем")
            _LOGGER.info("  - parse_status_string: Парсинг строки статуса")
            _LOGGER.info("\n📌 Параметры для set_mode и set_delayed_mode:")
            _LOGGER.info("  --mode: Режим работы мультиварки")
            _LOGGER.info("  --target_temp: Целевая температура")
            _LOGGER.info("  --boil_time: Время кипения")
            _LOGGER.info("  --subprog: Подрежим")
            _LOGGER.info("  --hours: Часы")
            _LOGGER.info("  --minutes: Минуты")
            _LOGGER.info("  --dhours: Часы задержки")
            _LOGGER.info("  --dminutes: Минуты задержки")
            _LOGGER.info("  --heat: Нагрев")
            _LOGGER.info("\n📌 Параметры для parse_status_string:")
            _LOGGER.info("  --status_string: Строка статуса для парсинга")
    finally:
        if 'library' in locals():
            await library.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
