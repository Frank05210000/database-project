"""把資料庫拒絕（CHECK、UNIQUE、外鍵、trigger 的 RAISE）轉成 HTTP 409 與可讀訊息。"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError

CONSTRAINT_MESSAGES = {
    "users_loginid_key": "BR-01：loginid 已被使用",
    "product_price_check": "BR-04：商品價格須大於 0",
    "product_stock_check": "BR-06：庫存不得為負數",
    "cart_item_quantity_check": "BR-05：數量必須是大於 0 的整數",
    "order_item_quantity_check": "BR-05：數量必須是大於 0 的整數",
    "return_item_order_id_item_no_fkey": "BR-25：只能退這張訂單裡的商品",
    "return_request_order_id_key": "BR-25：每筆訂單只能提出一次退貨申請",
    "discount_check": "BR-14：開始日期須小於或等於結束日期",
    "discount_rate_check": "BR-15：折扣率須介於 0 與 1 之間",
    "discount_min_amount_check": "BR-17：運費折扣的門檻金額須大於 0",
    "store_review_rating_check": "BR-24：評分須為 1 至 5 的整數",
    "store_review_pkey": "BR-24：每筆訂單對每間商店只能評價一次",
}


def db_error_message(exc: DBAPIError) -> str:
    orig = exc.orig
    diag = getattr(orig, "diag", None)
    constraint = getattr(diag, "constraint_name", None) if diag else None
    if constraint and constraint in CONSTRAINT_MESSAGES:
        return CONSTRAINT_MESSAGES[constraint]
    primary = getattr(diag, "message_primary", None) if diag else None
    if primary:
        sqlstate = getattr(orig, "sqlstate", "")
        if sqlstate == "23503":
            return f"BR-20：資料已被其他紀錄引用，無法刪除或修改（{primary}）"
        return primary
    return str(orig).split("\n")[0]


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(DBAPIError)
    async def handle_db_error(request: Request, exc: DBAPIError):
        return JSONResponse(status_code=409, content={"detail": db_error_message(exc)})
