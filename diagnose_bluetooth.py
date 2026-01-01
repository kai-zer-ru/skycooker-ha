#!/usr/bin/env python3
"""
Скрипт для диагностики Bluetooth подключения SkyCooker
"""

import asyncio
import logging
from bleak import BleakScanner

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scan_devices():
    """Сканирование Bluetooth устройств"""
    logger.info("🔍 Начинаем сканирование Bluetooth устройств...")
    
    try:
        devices = await BleakScanner.discover(timeout=15.0)
        logger.info(f"✅ Найдено {len(devices)} Bluetooth устройств")
        
        # Фильтрация устройств SkyCooker
        skycooker_devices = []
        for device in devices:
            name = device.name or "Unknown"
            address = device.address
            
            # Проверяем по имени
            if 'RMC' in name or 'SkyCooker' in name or 'Redmond' in name:
                skycooker_devices.append(device)
                logger.info(f"🎯 Найдено устройство SkyCooker: {name} - {address} (RSSI: {device.rssi})")
            
            # Проверяем по MAC адресу (если известен)
            if address == "DA:D8:9F:9E:0B:4C":
                skycooker_devices.append(device)
                logger.info(f"🎯 Найдено целевое устройство по MAC: {name} - {address} (RSSI: {device.rssi})")
        
        if not skycooker_devices:
            logger.warning("⚠️ Устройства SkyCooker не найдены")
            logger.info("📋 Все найденные устройства:")
            for device in devices:
                logger.info(f"  - {device.name or 'Unknown'}: {device.address} (RSSI: {device.rssi})")
        else:
            logger.info(f"✅ Найдено {len(skycooker_devices)} устройств SkyCooker")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при сканировании: {e}")
        return False
    
    return True

async def check_bluetooth_adapter():
    """Проверка состояния Bluetooth адаптера"""
    logger.info("🔧 Проверка Bluetooth адаптера...")
    
    try:
        # Проверка доступности адаптера
        scanner = BleakScanner()
        await scanner.start()
        await asyncio.sleep(1.0)
        await scanner.stop()
        logger.info("✅ Bluetooth адаптер доступен")
        return True
    except Exception as e:
        logger.error(f"❌ Bluetooth адаптер недоступен: {e}")
        return False

async def main():
    """Главная функция"""
    logger.info("🚀 Запуск диагностики Bluetooth SkyCooker")
    logger.info("=" * 50)
    
    # Проверка адаптера
    adapter_ok = await check_bluetooth_adapter()
    if not adapter_ok:
        logger.error("❌ Диагностика прервана: Bluetooth адаптер недоступен")
        return
    
    # Сканирование устройств
    scan_ok = await scan_devices()
    
    logger.info("=" * 50)
    if scan_ok:
        logger.info("✅ Диагностика завершена успешно")
        logger.info("💡 Рекомендации:")
        logger.info("1. Убедитесь, что устройство включено и в режиме сопряжения")
        logger.info("2. Проверьте расстояние до устройства (рекомендуется 5-10 метров)")
        logger.info("3. Убедитесь, что устройство не подключено к другому приложению")
    else:
        logger.error("❌ Диагностика завершена с ошибками")

if __name__ == "__main__":
    asyncio.run(main())