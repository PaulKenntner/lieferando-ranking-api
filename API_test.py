from app.api.routes import get_rank

async def test_get_rank():
    restaurant_slug = "loco-chicken-i-frechen"
    result = await get_rank(restaurant_slug)
    print(result)

test_get_rank()