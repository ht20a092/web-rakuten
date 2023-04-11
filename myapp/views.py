import requests
from django.shortcuts import redirect
from .models import FavoriteProduct
from django.shortcuts import render
from apscheduler.schedulers.background import BackgroundScheduler
from django.shortcuts import render, redirect
from django.http import HttpResponse

def search_products(query):
    app_id = "1072722666659103303"
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": app_id,
        "format": "json",
        "keyword": query,
    }
    response = requests.get(url, params=params)
    result = response.json()
    return result["Items"]

def get_product_details(product_id):
    app_id = "1072722666659103303"
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"  # Fixed API endpoint
    params = {
        "applicationId": app_id,
        "format": "json",
        "itemCode": product_id,
    }
    response = requests.get(url, params=params)
    result = response.json()
    if 'Items' in result and len(result['Items']) > 0:
        return result["Items"][0]["Item"]
    else:
        return None

def add_favorite(request, product_id):
    if request.method == "POST":
        product = get_product_details(product_id)
        if product is not None:
            favorite = FavoriteProduct(
                product_id=product_id,
                name=product["itemName"],
                image_url=product["mediumImageUrls"][0]["imageUrl"],
                price=product["itemPrice"],
                initial_price=product["itemPrice"],  # Add this line
            )
            favorite.save()
        else:
            print(f"Product with id {product_id} not found.")
    return redirect("myapp:favorites")

def favorites(request):
    favorite_products = FavoriteProduct.objects.all()
    context = {"favorite_products": favorite_products}
    return render(request, "myapp/favorites.html", context)

def send_line_notify(message):
    access_token = "IbEECzOXdXCUl5xXS2svSf6rAAr8z7aSkYe9RLD7Six"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {"message": message}
    requests.post("https://notify-api.line.me/api/notify", headers=headers, data=data)

def check_price():
    favorite_products = FavoriteProduct.objects.all()
    for favorite_product in favorite_products:
        current_product = get_product_details(favorite_product.product_id)
        current_price = current_product["itemPrice"]
        if current_price < favorite_product.price:
            message = f"【価格変更】 {favorite_product.name} が {favorite_product.price} 円から {current_price} 円に下がりました。"
            send_line_notify(message)
            favorite_product.price = current_price
            favorite_product.save()

scheduler = BackgroundScheduler()
scheduler.add_job(check_price, "interval", hours=1)
scheduler.start()

def search(request):
    query = request.GET.get("query", "")
    products = []
    if query:
        products = search_products(query)
    return render(request, "myapp/search.html", {"products": products})

def remove_favorite(request, product_id):
    if request.method == "POST":
        favorite = FavoriteProduct.objects.filter(product_id=product_id)
        if favorite.exists():
            favorite.delete()
    return redirect("myapp:favorites")