import requests
from django.conf import settings
from django.core.mail import send_mail
from apscheduler.schedulers.background import BackgroundScheduler
from myapp.models import Product, UserProfile
from .views import send_line_notify

def get_json_from_api(url, params):
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        return response.json()
    except requests.exceptions.HTTPError as errh:
        print ("HTTP Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print ("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print ("Timeout Error:", errt)
    except requests.exceptions.RequestException as err:
        print ("Error:", err)
    return None

def search_products_on_rakuten(query="", item_code=""):
    app_id = "1072722666659103303"
    url = "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20170706"
    params = {
        "applicationId": app_id,
        "format": "json",
        "keyword": query,
    }
    result = get_json_from_api(url, params)
    return result["Items"] if result else []

def search_products_on_yahoo(query=""):
    YAHOO_APP_ID = "dj00aiZpPTdpT2VIRUxmWGpsdiZzPWNvbnN1bWVyc2VjcmV0Jng9ZmI-"  
    url = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"
    params = {
        "appid": YAHOO_APP_ID,
        "query": query,
    }
    response = requests.get(url, params=params)

    try:
        result = response.json()
        print(result)  # 全てのレスポンスを確認
        hits = result["hits"]
        return hits
    except ValueError:
        print("Error decoding JSON data from Yahoo API")
        return []
    except KeyError:
        print("Key 'ResultSet' not found in the response")
        return []


def check_price():
    users = UserProfile.objects.all()
    for user in users:
        favorite_products = user.favorite_products.all()
        for product in favorite_products:
            if product.platform == "rakuten":
                item = search_products_on_rakuten(item_code=product.product_id)
            else:
                item = search_products_on_yahoo(item_code=product.product_id)

            if item and item["itemPrice"] < product.price:
                message = f"{product.name}の価格が下がりました！\n新しい価格: {item['itemPrice']}円\n詳細ページ: {product.url}"
                send_line_notify(message)
                print(message)
                product.price = item["itemPrice"]
                product.save()

def send_test_line_message():
    print("Sending test LINE message...")
    message = "テストです"
    response = send_line_notify(message)
    if response.status_code != 200:
        print(f"Error sending LINE message: {response.status_code}, {response.text}")

scheduler = BackgroundScheduler()
scheduler.add_job(check_price, "interval", hours=1)

#if settings.DEBUG:  # Only send test messages in debug mode
#    scheduler.add_job(send_test_line_message, "interval", minutes=1)

scheduler.start()

