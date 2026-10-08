# -*- coding: utf-8 -*-
{
    'name': "Custom Dymo Print Out",

    'summary': "Custom barcode generation, variant images, send/validate stock transfers",

    'description': """
    - Auto-generates barcodes using product base barcode + 3-digit serial extension
    - Variant-level independent images
    - Stock transfer Send → Validate two-step workflow
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    'category': 'Inventory',
    'version': '19.0.1.2.0',

    'depends': ['base', 'product', 'stock', 'stock_barcode'],

    'data': [
        'data/barcode_sequence.xml',
        'data/barcode_actions.xml',
        'views/views.xml',
        'views/templates.xml',
        'views/stock_picking_views.xml',
    ],

    'assets': {
        'web.assets_backend': [
            'custom_dymo_print_out/static/src/barcode_picking_patch.js',
        ],
    },

    'demo': [
        'demo/demo.xml',
    ],
}
