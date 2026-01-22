import os
import logging
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from telegram_bot_app.models.salon import Salon
from telegram_bot_app.core.config import settings

logger = logging.getLogger(__name__)


class GISService:
    """Сервис для работы с 2GIS API"""

    def __init__(self):
        self.api_key = settings.twogis_api_key
        self.base_url = "https://catalog.api.2gis.com/3.0/items/geocode"
        logger.info("GISService initialized")

    def _extract_city(self, address: str) -> str:
        """
        Извлекает город из адреса для формирования URL 2GIS

        Args:
            address: Полный адрес

        Returns:
            str: Название города на латинице для URL
        """
        logger.debug(f"Extracting city from address: {address}")

        # Список городов Казахстана и их URL представления
        city_mapping = {
            'алматы': 'almaty',
            'астана': 'astana',
            'нур-султан': 'astana',
            'шымкент': 'shymkent',
            'караганда': 'karaganda',
            'актобе': 'aktobe',
            'тараз': 'taraz',
            'павлодар': 'pavlodar',
            'усть-каменогорск': 'uskamen',
            'семей': 'semey',
            'атырау': 'atyrau',
            'кызылорда': 'kyzylorda',
            'кокшетау': 'kokshetau',
            'талдыкорган': 'taldykorgan',
            'экибастуз': 'ekibastuz',
            'рудный': 'rudny',
            'петропавловск': 'petropavlovsk',
            'темиртау': 'temirtau',
            'туркестан': 'turkestan',
            'костанай': 'kostanay',
            'кызыл-орда': 'kyzylorda',
            'уральск': 'uralsk',
            'актау': 'aktau',
            'жанаозен': 'zhanaozen',
            'балхаш': 'balkhash',
            'жезказган': 'zhezkazgan',
            'сатпаев': 'satpayev',
            'риддер': 'ridder',
            'степногорск': 'stepnogorsk'
        }

        address_lower = address.lower()
        logger.debug(f"Address in lowercase: {address_lower}")

        # Ищем город в адресе
        for city_ru, city_url in city_mapping.items():
            if city_ru in address_lower:
                logger.info(f"City '{city_ru}' found in address, mapped to '{city_url}'")
                return city_url

        # Если город не найден, пробуем извлечь из последних слов
        words = address_lower.split()
        if len(words) >= 2:
            # Проверяем последние два слова
            last_two = ' '.join(words[-2:])
            if last_two in city_mapping:
                logger.info(f"City '{last_two}' found in last two words, mapped to '{city_mapping[last_two]}'")
                return city_mapping[last_two]

        # Если ничего не найдено, возвращаем Алматы как крупнейший город Казахстана
        logger.warning(f"City not found in address '{address}', using default: almaty")
        return 'almaty'

    async def search_by_address(self, address: str) -> Optional[str]:
        """
        Поиск объекта по адресу через 2GIS API

        Args:
            address: Адрес для поиска

        Returns:
            Optional[str]: Ссылка на объект 2GIS или None если не найдено
        """
        logger.info(f"Starting 2GIS search for address: {address}")

        if not self.api_key:
            logger.error("2GIS API key (TWOGIS_API_KEY) not found in settings")
            return None

        logger.debug(f"Using API key: {self.api_key[:10]}...")

        params = {
            'q': address,
            'fields': 'items.id,items.full_name',
            'key': self.api_key
        }

        logger.debug(f"Request params: {params}")

        try:
            async with httpx.AsyncClient() as client:
                logger.debug(f"Sending GET request to {self.base_url}")
                response = await client.get(self.base_url, params=params, timeout=10.0)

                logger.debug(f"Response status code: {response.status_code}")
                response.raise_for_status()

                data = response.json()
                logger.debug(f"Response data: {data}")

                if data.get('result') and data['result'].get('items'):
                    items_count = len(data['result']['items'])
                    logger.info(f"Found {items_count} items in 2GIS response")

                    # Берем первый найденный результат
                    first_item = data['result']['items'][0]
                    logger.debug(f"First item: {first_item}")

                    if 'id' in first_item:
                        # Определяем город из адреса
                        city = self._extract_city(address)
                        # Формируем ссылку на 2GIS вручную
                        item_id = first_item['id']
                        gis_url = f"https://2gis.kz/{city}/geo/{item_id}"
                        logger.info(f"Generated 2GIS link for address '{address}': {gis_url}")
                        return gis_url
                    else:
                        logger.warning(f"Item ID not found in first result for address: {address}")

                logger.warning(f"No 2GIS results found for address: {address}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"HTTP error when searching 2GIS for address '{address}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Unexpected error when searching 2GIS for address '{address}': {e}", exc_info=True)
            return None


async def update_gis_link(salon: Salon, db: AsyncSession) -> bool:
    """
    Обновляет ссылку на 2GIS для салона

    Args:
        salon: Объект салона
        db: Сессия базы данных

    Returns:
        bool: True если обновление успешно, False если произошла ошибка
    """
    logger.info(f"Starting GIS link update for salon ID: {salon.id}")

    if not salon.address:
        logger.warning(f"Salon {salon.id} has no address, skipping GIS link update")
        return False

    logger.debug(f"Salon {salon.id} address: {salon.address}")

    # Проверяем, нужно ли обновлять ссылку
    if salon.gis_link:
        logger.debug(f"Salon {salon.id} already has GIS link: {salon.gis_link}")
        # Если ссылка уже есть, проверяем, изменился ли адрес
        # Для этого нужно получить оригинальный адрес из базы
        from telegram_bot_app.crud.salon import SalonCRUD
        salon_crud = SalonCRUD(db)
        original_salon = await salon_crud.get(salon.id)

        if original_salon and original_salon.address == salon.address:
            logger.info(f"Salon {salon.id} address hasn't changed, keeping existing GIS link")
            return True
        else:
            logger.info(f"Salon {salon.id} address has changed, updating GIS link")

    gis_service = GISService()
    gis_link = await gis_service.search_by_address(salon.address)

    if gis_link:
        salon.gis_link = gis_link
        logger.debug(f"Committing changes to database for salon {salon.id}")
        await db.commit()
        await db.refresh(salon)
        logger.info(f"Successfully updated GIS link for salon {salon.id}: {gis_link}")
        return True
    else:
        # Если поиск не удался, оставляем поле пустым
        salon.gis_link = None
        logger.debug(f"Setting GIS link to None for salon {salon.id}")
        await db.commit()
        await db.refresh(salon)
        logger.warning(f"Failed to find GIS link for salon {salon.id}, set to None")
        return False