import requests
from datetime import datetime, timedelta

def get_bonds_with_filters(
    credit_rating=None,
    min_coupon=None,
    min_yield=None,
    years_to_maturity=None
):
    url = "https://iss.moex.com/iss/engines/stock/markets/bonds/securities.json"
    params = {'iss.meta': 'off'}
    if credit_rating:
        params['creditrating'] = credit_rating.upper()
    if min_coupon is not None:
        params['couponvalue_ge'] = min_coupon
    if min_yield is not None:
        params['yieldtomaturity_ge'] = min_yield
    if years_to_maturity:
        today = datetime.now()
        params['matdate_from'] = today.strftime('%Y-%m-%d')
        params['matdate_to']   = (today + timedelta(days=365 * years_to_maturity)).strftime('%Y-%m-%d')
    try:
        r = requests.get(url, params=params)
        r.raise_for_status()
        sec = r.json().get('securities', {})
        cols, rows = sec.get('columns', []), sec.get('data', [])
        return [dict(zip(cols, row)) for row in rows]
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return []

def get_bonds_with_ticker(ticker):
    url = f"https://iss.moex.com/iss/engines/stock/markets/bonds/securities/{ticker}.json"
    try:
        resp = requests.get(url, params={'iss.meta': 'off'})
        resp.raise_for_status()
        j = resp.json()

        # Основные данные
        sec = j.get('securities', {})
        cols, rows = sec.get('columns', []), sec.get('data', [])
        if not rows:
            return None
        data = dict(zip(cols, rows[0]))

        # Рыночные данные по торгам
        md = j.get('marketdata', {})
        mcols, mrows = md.get('columns', []), md.get('data', [])
        market = dict(zip(mcols, mrows[0])) if mrows else {}

        # Доходности
        yld = j.get('marketdata_yields', {})
        ycols, yrows = yld.get('columns', []), yld.get('data', [])
        yields = dict(zip(ycols, yrows[0])) if yrows else {}
    except Exception as e:
        print(f"Error fetching ticker: {e}")
        return "Ошибка"
    return data, market, yields