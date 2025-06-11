import requests
import json
from typing import List, Dict, Optional
import time

class MoexBondsAPI:
    """Класс для работы с API Московской Биржи для облигаций"""

    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def _make_request(self, url: str, params: dict = None) -> Optional[dict]:
        """Выполнить HTTP запрос с обработкой ошибок"""
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к {url}: {e}")
            return None

    def get_all_bonds(self, board_id: str = "TQCB", limit: int = None) -> List[Dict]:
        """
        Получить список всех облигаций

        Args:
            board_id: Режим торгов (TQCB - корпоративные, TQOB - государственные)
            limit: Максимальное количество записей

        Returns:
            Список словарей с данными об облигациях
        """
        url = f"{self.base_url}/engines/stock/markets/bonds/boards/{board_id}/securities.json"

        params = {
            "iss.meta": "off",
            "iss.only": "securities,marketdata_yields"
        }

        if limit:
            params["limit"] = limit

        data = self._make_request(url, params)
        if not data:
            return []

        bonds = []

        # Обработка основных данных об облигациях
        securities = data.get('securities', {})
        securities_columns = securities.get('columns', [])
        securities_data = securities.get('data', [])

        # Обработка данных о доходности
        yields = data.get('marketdata_yields', {})
        yields_columns = yields.get('columns', [])
        yields_data = yields.get('data', [])

        # Создаем словарь доходностей по SECID
        yields_dict = {}
        if yields_columns and yields_data:
            secid_idx = yields_columns.index('SECID') if 'SECID' in yields_columns else None
            if secid_idx is not None:
                for yield_row in yields_data:
                    if len(yield_row) > secid_idx and yield_row[secid_idx]:
                        secid = yield_row[secid_idx]
                        yield_info = {}
                        for i, col in enumerate(yields_columns):
                            if i < len(yield_row):
                                yield_info[col.lower()] = yield_row[i]
                        yields_dict[secid] = yield_info

        # Формируем список облигаций
        for row in securities_data:
            bond = {}

            # Основные данные
            for i, col in enumerate(securities_columns):
                if i < len(row):
                    bond[col.lower()] = row[i]

            # Добавляем данные о доходности
            secid = bond.get('secid')
            if secid and secid in yields_dict:
                bond.update(yields_dict[secid])

            bonds.append(bond)

        return bonds

    def get_bond_by_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Получить информацию об облигации по тикеру

        Args:
            ticker: Тикер облигации (например, RU000A0JXPD9)

        Returns:
            Словарь с данными об облигации или None
        """
        url = f"{self.base_url}/engines/stock/markets/bonds/securities/{ticker}.json"

        params = {
            "iss.meta": "off",
            "iss.only": "securities,marketdata,marketdata_yields"
        }

        data = self._make_request(url, params)
        if not data:
            return None

        bond_info = {}

        # Основные данные
        securities = data.get('securities', {})
        if securities.get('data') and securities.get('columns'):
            row = securities['data'][0]
            for i, col in enumerate(securities['columns']):
                if i < len(row):
                    bond_info[col.lower()] = row[i]

        # Рыночные данные
        marketdata = data.get('marketdata', {})
        if marketdata.get('data') and marketdata.get('columns'):
            row = marketdata['data'][0]
            for i, col in enumerate(marketdata['columns']):
                if i < len(row):
                    bond_info[f"market_{col.lower()}"] = row[i]

        # Данные о доходности
        yields = data.get('marketdata_yields', {})
        if yields.get('data') and yields.get('columns'):
            row = yields['data'][0]
            for i, col in enumerate(yields['columns']):
                if i < len(row):
                    bond_info[f"yield_{col.lower()}"] = row[i]

        return bond_info

    def filter_bonds(self, bonds: List[Dict], filters: Dict) -> List[Dict]:
        """
        Фильтровать облигации по заданным критериям

        Args:
            bonds: Список облигаций
            filters: Словарь с критериями фильтрации

        Returns:
            Отфильтрованный список облигаций
        """
        filtered_bonds = []

        for bond in bonds:
            include_bond = True

            # Фильтр по минимальной купонной доходности
            if 'min_coupon_percent' in filters:
                coupon_percent = bond.get('couponpercent')
                if coupon_percent is None or float(coupon_percent) < filters['min_coupon_percent']:
                    include_bond = False

            # Фильтр по максимальной купонной доходности
            if 'max_coupon_percent' in filters:
                coupon_percent = bond.get('couponpercent')
                if coupon_percent is None or float(coupon_percent) > filters['max_coupon_percent']:
                    include_bond = False

            # Фильтр по минимальной эффективной доходности
            if 'min_effective_yield' in filters:
                effective_yield = bond.get('effectiveyield')
                if effective_yield is None or float(effective_yield) < filters['min_effective_yield']:
                    include_bond = False

            # Фильтр по максимальной эффективной доходности
            if 'max_effective_yield' in filters:
                effective_yield = bond.get('effectiveyield')
                if effective_yield is None or float(effective_yield) > filters['max_effective_yield']:
                    include_bond = False

            # Фильтр по статусу (активные облигации)
            if 'status' in filters:
                if bond.get('status') != filters['status']:
                    include_bond = False

            # Фильтр по минимальной дюрации
            if 'min_duration' in filters:
                duration = bond.get('duration')
                if duration is None or float(duration) < filters['min_duration']:
                    include_bond = False

            # Фильтр по максимальной дюрации
            if 'max_duration' in filters:
                duration = bond.get('duration')
                if duration is None or float(duration) > filters['max_duration']:
                    include_bond = False

            # Фильтр по дате погашения (исключаем уже погашенные)
            if 'exclude_matured' in filters and filters['exclude_matured']:
                matdate = bond.get('matdate')
                if matdate and matdate != '0000-00-00':
                    from datetime import datetime
                    try:
                        mat_date = datetime.strptime(matdate, '%Y-%m-%d')
                        if mat_date < datetime.now():
                            include_bond = False
                    except:
                        pass

            if include_bond:
                filtered_bonds.append(bond)

        return filtered_bonds

    def format_bond_info(self, bond: Dict) -> str:
        """Форматировать информацию об облигации для вывода"""
        secid = bond.get('secid', 'N/A')
        shortname = bond.get('shortname', 'N/A')
        coupon_percent = bond.get('couponpercent', 'N/A')
        effective_yield = bond.get('effectiveyield', 'N/A')
        matdate = bond.get('matdate', 'N/A')
        duration = bond.get('duration', 'N/A')

        # Пытаемся получить текущую цену
        price = bond.get('market_last') or bond.get('market_waprice') or bond.get('prevprice') or 'N/A'

        return f"""
📊 {shortname} ({secid})
💰 Купонная доходность: {coupon_percent}%
📈 Эффективная доходность: {effective_yield}%
💵 Цена: {price}
📅 Погашение: {matdate}
⏱️ Дюрация: {duration} дней
🔗 ISIN: {bond.get('isin', 'N/A')}
        """.strip()

# Функции для использования в Telegram боте
def get_bonds_with_ticker(ticker: str) -> Dict:
    """Получить информацию об облигации по тикеру"""
    api = MoexBondsAPI()
    return api.get_bond_by_ticker(ticker)

def get_bonds_with_filters(filters: Dict) -> List[Dict]:
    """Получить облигации по фильтрам"""
    api = MoexBondsAPI()

    # Получаем все корпоративные облигации
    all_bonds = api.get_all_bonds(board_id="TQCB")

    # Применяем фильтры
    filtered_bonds = api.filter_bonds(all_bonds, filters)

    return filtered_bonds

def format_bonds_list(bonds: List[Dict], limit: int = 10) -> str:
    """Форматировать список облигаций для вывода"""
    if not bonds:
        return "Не найдено облигаций по заданным критериям"

    api = MoexBondsAPI()
    result = f"Найдено {len(bonds)} облигаций. Показываю первые {min(limit, len(bonds))}:\n\n"

    for i, bond in enumerate(bonds[:limit]):
        result += f"{i+1}. {api.format_bond_info(bond)}\n\n"

    return result
