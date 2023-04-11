import unittest
from unittest.mock import MagicMock
from myapp import tasks, views
from myapp.models import Product, UserProfile

class TestTasks(unittest.TestCase):

    def test_check_favorite_products_price(self):
        tasks.search_products_on_rakuten = MagicMock(return_value=None)
        tasks.search_products_on_yahoo = MagicMock(return_value=None)
        tasks.FavoriteProduct.objects.all = MagicMock(return_value=[])
        tasks.check_favorite_products_price()
        tasks.search_products_on_rakuten.assert_called()
        tasks.search_products_on_yahoo.assert_called()

class TestViews(unittest.TestCase):

    def test_search_products(self):
        query = "test_query"
        views.requests.get = MagicMock()
        views.search_products(query)
        views.requests.get.assert_called()

    def test_get_product_details(self):
        product_id = "test_id"
        views.requests.get = MagicMock()
        views.get_product_details(product_id)
        views.requests.get.assert_called()

    def test_send_line_notify(self):
        message = "test_message"
        views.requests.post = MagicMock()
        views.send_line_notify(message)
        views.requests.post.assert_called()

    def test_check_price(self):
        views.FavoriteProduct.objects.all = MagicMock(return_value=[])
        views.check_price()
        views.FavoriteProduct.objects.all.assert_called()

if __name__ == '__main__':
    unittest.main()
