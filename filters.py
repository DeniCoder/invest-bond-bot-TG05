import requests
from datetime import datetime, timedelta

def get_bonds_with_filters(
    credit_rating=None,
    min_coupon=None,
    min_yield=None,
    years_to_maturity=None
):
    url = "https://iss.moex.com/iss/engines/stock/markets/bonds/securities.json"
    params = {'limit': 100, 'iss.meta': 'off'}
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
