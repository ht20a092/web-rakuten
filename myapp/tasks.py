import requests
from django.conf import settings
from django.core.mail import send_mail
from apscheduler.schedulers.background import BackgroundScheduler
from myapp.models import Product, UserProfile
from .views import send_line_notify
from .views import search_product_details_on_rakuten
from .views import search_product_details_on_yahoo

def search_products_on_yahoo_with_query(query=""):
    app_id = "dj00aiZpPTdpT2VIRUxmWGpsdiZzPWNvbnN1bWVyc2VjcmV0Jng9ZmI-"  
    url = f"https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch?appid={app_id}&query={query}"
    response = requests.get(url)
    result = response.json()
    if "hits" in result:
        return result["hits"]
    else:
        return None


def get_json_from_api(url, params):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print ("Error:", err)
    return None

def search_product_on_rakuten(item_code=""):
    app_id = "1072722666659103303"
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": app_id,
        "format": "json",
        "itemCode": item_code,
    }
    result = get_json_from_api(url, params)
    return result["Items"][0] if result and result["Items"] else None

def search_product_on_yahoo(product_name=""):
    YAHOO_APP_ID = "dj00aiZpPTdpT2VIRUxmWGpsdiZzPWNvbnN1bWVyc2VjcmV0Jng9ZmI-"  
    url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    params = {
        "appid": YAHOO_APP_ID,
        "query": product_name,  # itemCodeからqueryに変更
    }
    result = get_json_from_api(url, params)

    return result["hits"][0] if result and result["hits"] else None

def send_notify_email(subject, message, recipient_list):
    """
    Send notification email to user.
    """
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        recipient_list,
    )


def check_price():
    products = Product.objects.all()
    for product in products:
        # 商品が楽天から取得されたものならば
        if product.platform == 'rakuten':
            item = search_product_on_rakuten(product.product_id)
            if item and item["Item"]["itemPrice"] != product.price:  # 価格が下がった時に通知を送るために、新しい価格が元の価格よりも低いかをチェック
                message = f'{product.name}の値段が{product.price}から{item["Item"]["itemPrice"]}になりました'
                user_profiles = UserProfile.objects.filter(favorite_products=product)  # その商品をお気に入りにしている全てのユーザープロフィールを取得
                for user_profile in user_profiles:
                    send_notify_email("価格変動のお知らせ", message, [user_profile.user.email])  # 各ユーザーにメールを送る
                product.price = item["Item"]["itemPrice"]  # 商品の価格を更新
                product.save()  # 更新を保存
        # 商品がYahooから取得されたものならば
        elif product.platform == 'yahoo':
            item = search_product_on_yahoo(product.name)
            if item and item["price"] != product.price:  # 価格が下がった時に通知を送るために、新しい価格が元の価格よりも低いかをチェック
                message = f'{product.name}の値段が{product.price}から{item["price"]}になりました'
                user_profiles = UserProfile.objects.filter(favorite_products=product)  # その商品をお気に入りにしている全てのユーザープロフィールを取得
                for user_profile in user_profiles:
                    send_notify_email("価格変動のお知らせ", message, [user_profile.user.email])  # 各ユーザーにメールを送る
                product.price = item["price"]  # 商品の価格を更新
                product.save()  # 更新を保存





scheduler = BackgroundScheduler()
#scheduler.add_job(check_price, "interval", hours=1)
# scheduler.add_job(send_test_email, 'interval', minutes=1)
scheduler.add_job(check_price, "interval", minutes=1)
#if settings.DEBUG:
#    scheduler.add_job(send_test_line_message, "interval", minutes=1)

scheduler.start()