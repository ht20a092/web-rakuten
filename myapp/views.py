from django.shortcuts import redirect, render
from .models import Product, UserProfile
from django.http import HttpResponseRedirect
from django.urls import reverse
import json
import requests
from django.contrib.auth import authenticate, login as auth_login, logout
from django.http import HttpResponse
from django.contrib.auth.forms import UserCreationForm
from apscheduler.schedulers.background import BackgroundScheduler
from . import tasks
from urllib.parse import quote
from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm
from urllib.parse import unquote


RAKUTEN_APP_ID = "1072722666659103303"
YAHOO_APP_ID = "dj00aiZpPTdpT2VIRUxmWGpsdiZzPWNvbnN1bWVyc2VjcmV0Jng9ZmI-"



def search_product_details_on_rakuten(product_id):
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

def search_product_details_on_yahoo(name):
    app_id = "dj00aiZpPTdpT2VIRUxmWGpsdiZzPWNvbnN1bWVyc2VjcmV0Jng9ZmI-"
    url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={app_id}&query={name}"
    response = requests.get(url)

    if response.status_code != 200:
        return None

    try:
        result = response.json()
    except json.JSONDecodeError:
        return None

    # 'hits'が存在し、かつ一つ以上の結果があることを確認します
    if 'hits' in result and len(result['hits']) > 0:
        # 最初のヒットを取得します
        hit = result["hits"][0]
        product_info = {
            "name": hit.get("name"),
            "description": hit.get("description"),
            "url": hit.get("url"),
            "inStock": hit.get("inStock"),
            "code": hit.get("code"),
            "image": hit.get("image", {}).get("medium"),  # JSONの中のJSONにアクセス
            "price": hit.get("price")  # ここを修正し、priceにアクセスする
        }
        return product_info
    return None


def add_favorite(request, platform, product_id, product_name):
    product_name = urllib.parse.unquote(request.GET.get('product_name', ''))

    print("Platform: ", platform)
    print("Product ID: ", product_id)
    print("Product name: ", product_name)  # <--- ここを修正しました

    if request.method == "POST":
        # 商品情報を取得
        if platform == "rakuten":
            product_info = search_product_details_on_rakuten(product_id)  # 商品コードで検索
        elif platform == "yahoo":
            product_info = search_product_details_on_yahoo(product_name)  # 商品名で検索


        print("Product info: ", product_info)  # デバッグ情報を表示

        if product_info is not None:
            # Yahooと楽天で取得する情報の形式が異なるため、それぞれの場合で条件分岐
            if platform == 'yahoo':
                item_code = product_info["code"]
                item_name = product_info["name"]
                item_price = product_info["price"]
                item_image = product_info["image"]
                item_url = product_info["url"]
            elif platform == 'rakuten':
                item_code = product_info["itemCode"]
                item_name = product_info["itemName"]
                item_price = product_info["itemPrice"]
                item_image = product_info["mediumImageUrls"][0]["imageUrl"]
                item_url = product_info["itemUrl"]

            # お気に入りに追加
            favorite_product, created = Product.objects.get_or_create(
                product_id=item_code,
                defaults={
                    "name": item_name,
                    "price": item_price,
                    "image": item_image,
                    "url": item_url,
                    "platform": platform,
                },
            )

            request.user.userprofile.favorite_products.add(favorite_product)
            request.user.save()

    return HttpResponseRedirect(reverse("myapp:favorites"))






def favorites(request):
    if request.user.is_authenticated:
        user = request.user
        user_profile = UserProfile.objects.get(user=user)
        
        # 商品情報を取得し、リストに格納する
        rakuten_products_info = []
        yahoo_products_info = []
        favorite_products = user_profile.favorite_products.all()

        for favorite_product in favorite_products:
            product_info = {
                'product_id': favorite_product.product_id,
                'name': favorite_product.name,
                'image': favorite_product.image,
                'price': favorite_product.price,
                'url': favorite_product.url
            }
            
            # If product is from rakuten market
            if favorite_product.platform == 'rakuten':
                rakuten_products_info.append(product_info)
            # If product is from yahoo shopping
            elif favorite_product.platform == 'yahoo':
                yahoo_products_info.append(product_info)

        context = {'rakuten_products': rakuten_products_info, 'yahoo_products': yahoo_products_info}
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
        products = tasks.search_products_on_rakuten(query)  # この行を変更
    return render(request, "myapp/search.html", {"products": products})

def search_rakuten(request):
    query = request.GET.get("query", "")
    products = []
    if query:
        products = search_products_on_rakuten(query)
    return render(request, "myapp/search_rakuten.html", {"products": products})

def search_yahoo(request):
    query = request.GET.get('query', '')
    hits = []  
    if query:
        query = quote(query)
        hits = tasks.search_products_on_yahoo_with_query(query)  
    return render(request, 'myapp/search_yahoo.html', {'query': query, 'hits': hits})




def remove_favorite(request, platform, product_id):
    if request.method == "POST":
        user = request.user
        if user.is_authenticated:
            favorite = user.userprofile.favorite_products.filter(platform=platform, product_id=product_id)
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
    path("search/rakuten/", views.search_rakuten, name="search_rakuten"),  # 追加
    path("search/yahoo/", views.search_yahoo, name="search_yahoo"),        # 追加
    path("favorites/", views.favorites, name="favorites"),
    path('add_favorite/<str:platform>/<str:product_id>/<path:product_name>/', views.add_favorite, name='add_favorite'),
    path("remove_favorite/<str:platform>/<str:product_id>/", views.remove_favorite, name="remove_favorite"),
    path("about/", views.about, name="about"),
    # 他のルーティング...
]

def login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("myapp:search_rakuten")
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
    app_id = YAHOO_APP_ID
    if item_code:
        url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={app_id}&code={item_code}"
    else:
        url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={app_id}&query={query}"
    response = requests.get(url)
    result = response.json()
    if "hits" in result:
        if item_code:
            return result["hits"][0]
        else:
            return result["hits"]
    else:
        return None

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('myapp:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'myapp/register.html', {'form': form})