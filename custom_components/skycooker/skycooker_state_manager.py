#!/usr/local/bin/python3
# coding: utf-8

import asyncio
import logging
import traceback
from time import monotonic

from .const import *
from .skycooker_connection_manager import AuthError

_LOGGER = logging.getLogger(__name__)


class SkyCookerStateManager:
    """Класс для управления состоянием мультиварки."""
    
    def __init__(self, connection_manager, cooking_controller):
        self.connection_manager = connection_manager
        self.cooking_controller = cooking_controller
        self._stats = None
    
    async def update(self, tries=MAX_TRIES, force_stats=False, extra_action=None, commit=False):
        """Обновление состояния мультиварки."""
        try:
            async with self.connection_manager.update_lock:
                if self.connection_manager.disposed: return None
                _LOGGER.debug("🔄 Обновление состояния мультиварки")
                if not self.connection_manager.available: force_stats = True
                await self.connection_manager.connect_if_need()
              
                if extra_action: await extra_action
              
                try:
                    status = await self.connection_manager.get_status()
                    self.cooking_controller.status = status
                except Exception as e:
                    _LOGGER.warning(f"⚠️  Ошибка получения статуса: {e}")
                    self.cooking_controller.status = None
                    raise
              
                _LOGGER.debug("📊 Статус устройства успешно получен, команды не отправляются")
             
                await self.connection_manager.disconnect_if_need()
                self.connection_manager.add_stat(True)
             
                return True
    
        except Exception as ex:
            await self.connection_manager.disconnect()
            if hasattr(self.cooking_controller, 'target_program_name') and self.cooking_controller.target_program_name is not None and self.cooking_controller.last_set_target + TARGET_TTL < monotonic():
                _LOGGER.warning(f"⚠️  Не удалось установить режим {self.cooking_controller.target_program_name} в течение {TARGET_TTL} секунд, прекращаю попытки")
                self.cooking_controller.target_program_name = None
            if isinstance(ex, AuthError): return None
            self.connection_manager.add_stat(False)
            if tries > 1 and extra_action is None:
                _LOGGER.debug(f"🚫 {type(ex).__name__}: {str(ex)}, повтор #{MAX_TRIES - tries + 1}")
                await asyncio.sleep(TRIES_INTERVAL)
                return await self.update(tries=tries-1, force_stats=force_stats, extra_action=extra_action, commit=commit)
            else:
                _LOGGER.warning(f"⚠️  Не удалось обновить состояние, {type(ex).__name__}: {str(ex)}")
                _LOGGER.debug(traceback.format_exc())
            return False
    
    async def commit(self):
        """Применение изменений к устройству."""
        _LOGGER.debug("Committing changes")
        await self.update()
    
    @property
    def status_code(self):
        """Код статуса."""
        if not self.cooking_controller.status: return None
        return self.cooking_controller.status.status if self.cooking_controller.status.is_on else STATUS_OFF

    @property
    def auto_warm(self):
        """Статус автоподогрева."""
        if self.cooking_controller.status:
            return self.cooking_controller.status.auto_warm
        return None

    @property
    def subprog(self):
        """Текущая подпрограмма."""
        if self.cooking_controller.status:
            return self.cooking_controller.status.subprogram_id
        return None
    
    @property
    def success_rate(self):
        """Процент успешных операций."""
        return self.connection_manager.success_rate


class SkyCookerError(Exception):
    pass