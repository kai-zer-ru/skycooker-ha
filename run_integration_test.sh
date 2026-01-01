#!/bin/bash

echo "🚀 Запуск интеграционных тестов SkyCooker в Docker"
echo "=================================================="
echo ""

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция проверки наличия команды
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Проверка наличия Docker
echo -e "${BLUE}📋 Проверка окружения...${NC}"
if ! command_exists docker; then
    echo -e "${RED}❌ Docker не установлен${NC}"
    exit 1
fi

if ! command_exists docker-compose; then
    echo -e "${RED}❌ Docker Compose не установлен${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker и Docker Compose доступны${NC}"
echo ""

# Проверка наличия USB Bluetooth адаптера
echo -e "${BLUE}📋 Проверка Bluetooth адаптера...${NC}"
if ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | grep -q .; then
    echo -e "${GREEN}✅ USB устройства найдены:${NC}"
    ls -la /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | head -5
else
    echo -e "${YELLOW}⚠️  USB Bluetooth адаптер не найден${NC}"
    echo "Проверьте подключение Bluetooth адаптера"
fi

echo ""

# Проверка Bluetooth
echo -e "${BLUE}📋 Проверка Bluetooth...${NC}"
if command_exists hciconfig; then
    if hciconfig | grep -q "UP"; then
        echo -e "${GREEN}✅ Bluetooth адаптер активен${NC}"
        hciconfig | grep -A 2 "hci"
    else
        echo -e "${YELLOW}⚠️  Bluetooth адаптер не активен${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  hciconfig не доступен${NC}"
fi

echo ""

# Создание директории для конфигурации
echo -e "${BLUE}📋 Подготовка конфигурации...${NC}"
if [ ! -d "test_config" ]; then
    mkdir -p test_config
    echo -e "${GREEN}✅ Создана директория test_config${NC}"
else
    echo -e "${GREEN}✅ Директория test_config уже существует${NC}"
fi

echo ""

# Запуск Docker Compose
echo -e "${BLUE}📋 Запуск Docker контейнеров...${NC}"
echo -e "${YELLOW}🐳 Запуск Home Assistant и тестового окружения...${NC}"

docker-compose -f docker-compose.integration-test.yml down -v 2>/dev/null
docker-compose -f docker-compose.integration-test.yml up -d

echo ""

# Ожидание запуска контейнеров
echo -e "${BLUE}📋 Ожидание запуска контейнеров...${NC}"
sleep 10

# Проверка статуса контейнеров
echo -e "${BLUE}📋 Проверка статуса контейнеров...${NC}"
docker-compose -f docker-compose.integration-test.yml ps

echo ""

# Проверка логов Home Assistant
echo -e "${BLUE}📋 Проверка логов Home Assistant...${NC}"
echo -e "${YELLOW}Проверка запуска Home Assistant (ожидание 60 секунд)...${NC}"

timeout 60 bash -c 'until docker-compose -f docker-compose.integration-test.yml logs home-assistant-test | grep -q "Starting Home Assistant"; do sleep 2; done' 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Home Assistant запущен${NC}"
else
    echo -e "${YELLOW}⚠️  Home Assistant может еще запускаться${NC}"
fi

echo ""

# Проверка логов тестового контейнера
echo -e "${BLUE}📋 Проверка логов тестового контейнера...${NC}"
sleep 5
docker-compose -f docker-compose.integration-test.yml logs skycooker-test-runner

echo ""

# Открытие веб-интерфейса
echo -e "${BLUE}📋 Доступ к веб-интерфейсу:${NC}"
echo -e "${GREEN}🌐 Home Assistant: http://localhost:8123${NC}"
echo ""

# Инструкции по использованию
echo -e "${BLUE}📋 Инструкции по использованию:${NC}"
echo "1. Откройте http://localhost:8123 в браузере"
echo "2. Дождитесь полной загрузки Home Assistant"
echo "3. Перейдите в Настройки → Интеграции"
echo "4. Найдите и добавьте интеграцию SkyCooker"
echo "5. Проверьте обнаружение устройства"
echo ""

echo -e "${BLUE}📋 Для просмотра логов:${NC}"
echo "docker-compose -f docker-compose.integration-test.yml logs -f home-assistant-test"
echo ""

echo -e "${BLUE}📋 Для остановки тестов:${NC}"
echo "docker-compose -f docker-compose.integration-test.yml down -v"
echo ""

echo -e "${GREEN}🎉 Интеграционные тесты запущены!${NC}"
echo "Теперь вы можете протестировать интеграцию SkyCooker с реальным Bluetooth адаптером."