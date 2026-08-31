from db_xbomer import *

numbers_price = None  # Boshida bo'sh turadi


def get_numbers_price(session):
    global numbers_price
    if not numbers_price:
        # Bazadan hammasini olib, dictga aylantiramiz
        # Masalan: item.number - kalit, item.price - narx deb olsak
        items = session.query(Numbers_list).all()
        numbers_price = {item.country: item.price for item in items}

    if 'US' not in numbers_price:
        return 'xato'

print(get_numbers_price(session))