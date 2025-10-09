{
    'name': "Auto Barcode Generator",
    'version': '18.0.1.0.0',
    'summary': """Automatically generates a unique EAN13 barcode for products, with a manual button.""",
    'description': """
        This module extends the product management functionality in Odoo 18.
        - It automatically generates a unique EAN13 barcode for a product if one is not specified upon creation.
        - It adds a button next to the barcode field to manually generate a new unique barcode.
        - The generated barcode is a unique 13-digit number.
    """,
    'category': 'Inventory/Stock',
    'author': "Shimanto Mahmud",
    'license': 'AGPL-3',
    'depends': ['product'],
    'installable': True,
    'auto_install': False,
    'application': False,
    'data': [
        'views/product_template_views.xml',
    ],
}
