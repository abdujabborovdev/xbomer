from fastapi import APIRouter
from fastapi.responses import JSONResponse
from db_xbomer import *
from pydantic import BaseModel
from sqlalchemy import select
router = APIRouter()


@router.post('/api/v1/')
async def key_test(key: str):
    result = await session.execute(
        select(SecretApiKey).filter(SecretApiKey.secret_api_key == key)
    )
    secret_key = result.scalar_one_or_none()

    if not secret_key:
        return JSONResponse(status_code=401, content={'error_code': 'INVALID_KEY'})

    return {"status": True, "message": "Key topildi"}


@router.post('/api/v1/balance/')
async def get_balance(key: str, action: str):

    if action and action != 'balance':
        return JSONResponse(status_code=400,
                            content={
                                "error_code": "INVALID ACTION",
                            })

    secret_key = session.query(SecretApiKey).filter(SecretApiKey.secret_api_key == key).first()
    if not secret_key:
        return JSONResponse(status_code=401, content={
            "error_code": "Invalid API key",

    }, )

    user = session.query(User).filter(User.id == secret_key.user_telegram_id).first()
    if not user:
        return JSONResponse(
            status_code=404, content={"error_code": "USER NOT FOUND",
                                      "message": "User bazada topilmadi"}
        )


    return {"balance": user.hisob, "currency": "UZS"}
numbers_price = None
async def nomers_price(session):
    global numbers_price
    if not numbers_price:
        items = session.query(Numbers_list).all()
        numbers_price = {item.country: item.price for item in items}
    return numbers_price
class AccountRequest(BaseModel):
    key: str
    action: str
    country: str
# @router.post("/api/v1/accounts_get")
# async def get_accounts_get(data: AccountRequest):
#     key = data.key
#     action = data.action
#     country = data.country
#     secret_key = session.query(SecretApiKey).filter(SecretApiKey.secret_api_key == key).first()
#     if not secret_key:
#         return JSONResponse(status_code=401, content={'error_code': 'INVALID API KEY'})
#
#     if action and action != 'accounts_get':
#         return JSONResponse(status_code=400, content={'error_code': 'INVALID ACTION'})
#
#     number_list = await nomers_price(session)
#     if country not in number_list:
#         return JSONResponse(status_code=403, content={'error_code': 'INVALID COUNTRY'})
#     secret_key = session.query(SecretApiKey).filter(SecretApiKey.secret_api_key == key).first()
#
#     user = session.query(User).filter(User.id == secret_key.user_telegram_id).first()
#
#     if not user:
#         return JSONResponse(status_code=404, content={'error_code': 'USER NOT FOUND'})
#
#     current_hisob = int(user.hisob) if user.hisob is not None else 0
#     user.hisob = current_hisob

