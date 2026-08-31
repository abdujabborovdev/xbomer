

from fastapi import APIRouter
from pydantic import BaseModel

import aiohttp
from sqlalchemy import select
from starlette.responses import JSONResponse
from db_xbomer import *
from loader import *
SEENSMS_KEY = SEENSMS_KEY

router = APIRouter(prefix="/api/v1", tags=["v1"])
URL = 'https://seensms.uz/api/v1'

class TestRequest(BaseModel):
    key: str


@router.post("/")
async def test_endpoint(payload: TestRequest):
    async with async_session() as session:
        result = await session.execute(select(SecretApiKey).filter_by(secret_api_key=payload.key))
        secret_keys = result.scalars().first()
        if not payload.key:
            return JSONResponse(status_code=400, content={"status":False,
                                                          "error_code": "MISSING_API_KEY",
                                                          "message": "API kaliti ('key') yuborilmadi"
                                                          })
        if not secret_keys:
            print(secret_keys)
            return JSONResponse(status_code=401, content={"status":False,"error_code" : "INVALID_API_KEY",
                                                          "message" : "API kalit noto'g'ri yoki bloklangan"
                                                          })
        return {"status": True,
  "message": "✅ API ishlamoqda"
}


class BalanceRequest(BaseModel):
    key: str
    action: str
@router.post("/balance/")
async def balance_endpoint(payload: BalanceRequest):
    async with async_session() as session:
        result = await session.execute(select(SecretApiKey).filter_by(secret_api_key=payload.key))
        secret_keys = result.scalars().first()
        if not payload.key:
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "MISSING_API_KEY",
                                                          "message": "API kaliti ('key') yuborilmadi"
                                                          })

        if not secret_keys:
            print(secret_keys)
            return JSONResponse(status_code=401, content={"status": False, "error_code": "INVALID_API_KEY",
                                                          "message": "API kalit noto'g'ri yoki bloklangan"
                                                          })
        result_user = await session.execute(select(User).filter_by(id=secret_keys.user_telegram_id))
        user = result_user.scalars().first()
        if not payload.action:
            return JSONResponse(status_code=400, content={"status":False,
                                                          "error_code": "MISSING_ACTION",
                                                          "message": "action parametri topilmadi"})
        if payload.action != "balance":
            return JSONResponse(status_code=400, content={"status":False,
                                                          "error_code": "INVALID_ACTION",
                                                          "message": "Noma'lum 'action' qiymati yuborildi"})

        return {"status": True,
                "balance": user.hisob,
                "currency": "UZS"}




class AccountsRequest(BaseModel):
    key: str
    action: str
    country: str

@router.post("/accounts_get/")
async def accounts_get(payload: AccountsRequest):
    async with async_session() as session:
        result = await session.execute(select(SecretApiKey).filter_by(secret_api_key=payload.key))
        secret_keys = result.scalars().first()
        if not payload.key:
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "MISSING_API_KEY",
                                                          "message": "API kaliti ('key') yuborilmadi"
                                                          })

        if not secret_keys:
            print(secret_keys)
            return JSONResponse(status_code=401, content={"status": False, "error_code": "INVALID_API_KEY",
                                                          "message": "API kalit noto'g'ri yoki bloklangan"
                                                          })

        if not payload.action:
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "MISSING_ACTION",
                                                          "message": "action parametri topilmadi"})
        if payload.action != "accounts_get":
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "INVALID_ACTION",
                                                          "message": "Noma'lum 'action' qiymati yuborildi"})
        if not payload.country:
            return JSONResponse(status_code=400, content={"status": False,"error_code": "MISSING_COUNTRY",})
        result_user = await session.execute(select(User).filter_by(id=secret_keys.user_telegram_id))
        user = result_user.scalars().first()

        result = await session.execute(select(Numbers_list).filter_by(country=payload.country))
        country = result.scalars().first()
        if not country:
            return JSONResponse(status_code=400, content={"status": False,"error_code": "COUNTRY_NOT_SUPPORTED","message": "Ko'rsatilgan 'country' uchun raqam mavjud emas"})
        try:
            hisobi = int(user.hisob) if user.hisob is not None else 0
        except (ValueError, TypeError):
            hisobi = 0

        if hisobi < int(country.price):
            return JSONResponse(status_code=402, content={"status": False,"error_code": "INSUFFICIENT_BALANCE","message":"Balansda mablag' yetarli emas"})
        conn = aiohttp.TCPConnector(ssl=False)
        try:
            async with aiohttp.ClientSession(connector=conn) as sess:
                async with sess.post(URL, data={
                    'key': f'{SEENSMS_KEY}',
                    'action': 'accounts_get',
                    'country': f'{payload.country}',
                }) as r:
                    dat = await r.json()
        except Exception as e:
            return JSONResponse(status_code=404, content={"status": False,"error_code": "NUMBER_NOT_AVAILABLE","message":"Hozircha bo'sh raqam yo'q","xatolik":str(e)})
        if isinstance(dat, dict) and dat.get('number'):
            await session.refresh(user)
            current_hisob = int(user.hisob) if user.hisob is not None else 0
            user.hisob = current_hisob - country.price
            await session.commit()


            num_id_s = dat.get('id')
            num_id = int(num_id_s)
            num_country = dat.get('country')
            number = dat.get('number')

            new_number_order = Order_numbers(
                id=num_id,
                country=num_country,
                owner_number=user.id,
                number=number
            )
            session.add(new_number_order)
            await session.commit()
            return {"status": True,
                    "country": num_country,
                    "id": num_id,
                    "number": number,}
        else:
            return JSONResponse(status_code=404, content={"status": False,"error_code": "NUMBER_NOT_AVAILABLE","message":"Hozircha bo'sh raqam yo'q"})


class AccountsCodeRequest(BaseModel):
    key: str
    action: str
    order_id: int
@router.post("/accounts_code/")
async def accounts_code(payload: AccountsCodeRequest):
    async with async_session() as session:
        result = await session.execute(select(SecretApiKey).filter_by(secret_api_key=payload.key))
        secret_keys = result.scalars().first()
        if not payload.key:
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "MISSING_API_KEY",
                                                          "message": "API kaliti ('key') yuborilmadi"
                                                          })
        if not secret_keys:
            print(secret_keys)
            return JSONResponse(status_code=401, content={"status": False, "error_code": "INVALID_API_KEY",
                                                          "message": "API kalit noto'g'ri yoki bloklangan"
                                                          })

        if not payload.action:
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "MISSING_ACTION",
                                                          "message": "action parametri topilmadi"})
        if payload.action != "accounts_code":
            return JSONResponse(status_code=400, content={"status": False,
                                                          "error_code": "INVALID_ACTION",
                                                          "message": "Noma'lum 'action' qiymati yuborildi"})
        if not payload.order_id:
            return JSONResponse(status_code=400, content={"status": False,"error_code": "NOT_ORDER_ID",})
        result_order = await session.execute(select(Order_numbers).filter_by(id=payload.order_id))
        number = result_order.scalars().first()
        if not number:
            return JSONResponse(status_code=404, content={"status": False,"error_code": "ORDER_NOT_FOUND","message":"'order_id' bo'yicha buyurtma topilmadi"})
        if number.owner_number != secret_keys.user_telegram_id:
            return JSONResponse(status_code=404, content={"status": False,"error_code": "ORDER_NOT_FOUND","message":"'order_id' bo'yicha buyurtma topilmadi"})
        conn = aiohttp.TCPConnector(ssl=False)  # Mana bu yerda connector qo'shiladi
        async with aiohttp.ClientSession(connector=conn) as r:
            async with r.post(URL, data={
                'key': f'{SEENSMS_KEY}',
                'action': 'accounts_code',
                'id': payload.order_id,
            }) as r:
                dat = await r.json()

        if isinstance(dat, dict) and dat.get('status'):
            if dat.get('status') == 'OK':
                kodi = dat.get('code')
                number.status = 'OK'
                number.kod = kodi
                number.pas2 = dat.get('password')
                await session.commit()
                passw = dat.get('password')
                return {"status": True,"code":kodi,"id":payload.order_id,"password":passw}

            elif dat.get('status') == 'WAITING':
               return JSONResponse(status_code=408, content={"status": False,"error_code": "CODE_NOT_RECEIVED","message":"SMS-kod hali kelmadi, birozdan keyin qayta urinib ko'ring"})
            else:
                return JSONResponse(status_code=404, content={"status": False, "error_code": "ORDER_NOT_FOUND",
                                                              "message": "'order_id' bo'yicha buyurtma topilmadi"})
