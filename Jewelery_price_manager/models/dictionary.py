# -*- coding: utf-8 -*-
# dictionary.py

# Price field mapping for different gold/silver types
PRICE_FIELD_MAP = {
    '22k': 'gold_22k_price',
    '21k': 'gold_21k_price',
    '18k': 'gold_18k_price',
    'traditional': 'gold_traditional_price',
    'silver_22k': 'silver_22k_price',
    'silver_21k': 'silver_21k_price',
    'silver_18k': 'silver_18k_price',
    'silver_traditional': 'silver_traditional_price',
    'silver_italian': 'silver_italian_price',
}

# Selection options for karats
KARAT_SELECTION = [
    ('22k', '22 Karat'),
    ('21k', '21 Karat'),
    ('18k', '18 Karat'),
    ('traditional', 'Traditional'),
    ('silver_22k', '22K Silver'),
    ('silver_21k', '21K Silver'),
    ('silver_18k', '18K Silver'),
    ('silver_traditional', 'Traditional Silver'),
    ('silver_italian', 'Italian Silver'),
]

# Conversion constants
GRAMS_PER_BHORI = 11.664
ANA_PER_BHORI = 16
ROKTI_PER_ANA = 4
POINT_PER_ROKTI = 6
