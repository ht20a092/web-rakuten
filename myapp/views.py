from django.shortcuts import redirect, render
from .models import Product, UserProfile
from django.http import HttpResponseRedirect
from django.urls import reverse
import requests
from django.contrib.auth import authenticate, login as auth_login, logout
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm



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
        # 商品情報を取得
        product_info = get_product_details(product_id)
        if product_info is not None:
            # お気に入りに追加
            favorite_product, created = Product.objects.get_or_create(
                product_id=product_info["itemCode"],
                defaults={
                    "name": product_info["itemName"],
                    "price": product_info["itemPrice"],
                    "image": product_info["mediumImageUrls"][0]["imageUrl"],
                    "url": product_info["itemUrl"],
                    "platform": "rakuten",
                },
            )
            request.user.userprofile.favorite_products.add(favorite_product)
            request.user.save()

    return HttpResponseRedirect(reverse("myapp:favorites"))

def favorites(request):
    if request.user.is_authenticated:
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        favorite_products = user_profile.favorite_products.all()

        # 商品情報を取得し、リストに格納する
        products_info = []
        for favorite_product in favorite_products:
            product_info = {
                'product_id': favorite_product.product_id,
                'name': favorite_product.name,
                'image': favorite_product.image,
                'price': favorite_product.price,
                'url': favorite_product.url
            }
            products_info.append(product_info)

        # コンソールにお気に入り商品情報を出力
        print("お気に入り商品情報:", products_info)

        context = {'favorite_products': products_info}
        return render(request, 'myapp/favorites.html', context)
    else:
        return redirect('myapp:login')

def send_line_notify(message):
    url = 'https://notify-api.line.me/api/notify'
    token = 'IbEECzOXdXCUl5xXS2svSf6rAAr8z7aSkYe9RLD7Six'
    headers = {
        'Authorization': f'Bearer {token}'
    }
    data = {
        'message': message
    }
    response = requests.post(url, headers=headers, data=data)  # ここで response が定義されるべき
    print(f"Status code: {response.status_code}, Text: {response.text}")
    return response

def send_test_line_message():
    print("Sending test LINE message...")
    message = "テストです"
    response = send_line_notify(message)
    if response.status_code != 200:
        print(f"Error sending LINE message: {response.status_code}, {response.text}")

scheduler = BackgroundScheduler()
scheduler.start()

def search(request):
    query = request.GET.get("query", "")
    products = []
    if query:
        products = search_products(query)
    return render(request, "myapp/search.html", {"products": products})

def remove_favorite(request, product_id):
    if request.method == "POST":
        user = request.user
        if user.is_authenticated:
            favorite = user.userprofile.favorite_products.filter(product_id=product_id)
            if favorite.exists():
                user.userprofile.favorite_products.remove(favorite.first())
                user.save()
        return redirect("myapp:favorites")


def index(request):
    return render(request, "myapp/index.html")

def about(request):
    return render(request, "myapp/about.html")

from django.urls import path
from . import views

app_name = "myapp"
urlpatterns = [
    path("", views.index, name="index"),
    path("search/", views.search, name="search"),
    path("favorites/", views.favorites, name="favorites"),
    path("add_favorite/<str:product_id>/", views.add_favorite, name="add_favorite"),
    path("remove_favorite/<str:product_id>/", views.remove_favorite, name="remove_favorite"),
    path("about/", views.about, name="about"),
]

def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("myapp:index")
        else:
            return HttpResponse("ユーザー名またはパスワードが間違っています。")
    return render(request, "myapp/login.html")

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            return redirect("myapp:index")
    else:
        form = UserCreationForm()
    return render(request, "myapp/register.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect('myapp:index')

def search_products_on_rakuten(query="", item_code=""):
    app_id = RAKUTEN_APP_ID
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": app_id,
        "format": "json",
    }
    if query:
        params["keyword"] = query
    if item_code:
        params["itemCode"] = item_code

    response = requests.get(url, params=params)
    result = response.json()
    if "Items" in result:
        if item_code:
            return result["Items"][0]["Item"]
        else:
            return result["Items"]
    else:
        return None


def search_products_on_yahoo(query="", item_code=""):
    # ここに Yahoo!ショッピング用の関数を実装してください。
    pass