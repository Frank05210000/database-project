from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.errors import install_error_handlers
from app.routers import admin, auth, cart, discounts, orders, products, reports, returns, stores

app = FastAPI(title="FUWA FUWA e-Shop API", version="1.0.0",
              description="多門市寵物用品電子商店：AAS / PMS / SCS / OMS / DMS / RSS / STS")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
install_error_handlers(app)

# 訪客瀏覽的公開資料（商品、商店、進行中的折扣）讓 CDN 快取 30 秒，過期後先回舊資料再背景更新。
# 有登入（帶 Authorization）的請求一律不快取，庫存與價格仍由加入購物車、結帳時即時檢查。
PUBLIC_PREFIXES = ("/api/products", "/api/stores", "/api/discounts/active")


@app.middleware("http")
async def public_cache(request: Request, call_next):
    response = await call_next(request)
    if (request.method == "GET" and response.status_code == 200
            and "authorization" not in request.headers
            and request.url.path.startswith(PUBLIC_PREFIXES)):
        response.headers["Cache-Control"] = "public, s-maxage=30, stale-while-revalidate=300"
        response.headers["Vary"] = "Authorization"
    return response

app.include_router(auth.router, prefix="/api/auth", tags=["AAS 帳號"])
app.include_router(admin.router, prefix="/api/admin", tags=["AAS 平台管理"])
app.include_router(stores.router, prefix="/api/stores", tags=["STS 商店"])
app.include_router(products.router, prefix="/api/products", tags=["PMS 商品"])
app.include_router(cart.router, prefix="/api/cart", tags=["SCS 購物車"])
app.include_router(orders.router, prefix="/api/orders", tags=["OMS 訂單"])
app.include_router(returns.router, prefix="/api/returns", tags=["OMS 退貨"])
app.include_router(discounts.router, prefix="/api/discounts", tags=["DMS 折扣"])
app.include_router(reports.router, prefix="/api/reports", tags=["RSS 報表"])


@app.get("/api/health")
def health():
    return {"status": "ok"}
