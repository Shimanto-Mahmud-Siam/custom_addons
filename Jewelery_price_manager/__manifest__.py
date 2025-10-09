{
    'name': "Jewellery Price Manager",
    'author': "Shimanto Mahmud",
    'version': '1.0',
    'depends': [
        'base',
        'product',
        'website',
        'website_sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/product_views.xml',
        'views/gold_silver_prices_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': True,
    'description': """A custom module to manage jewellery prices based on gold and silver rates.""",
}
