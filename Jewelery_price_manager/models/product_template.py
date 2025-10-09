# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math
from . import dictionary as config   # import dictionary file

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Use dictionary values
    PRICE_FIELD_MAP = config.PRICE_FIELD_MAP

    product_karat = fields.Selection(config.KARAT_SELECTION, string='Karat')

    gold_silver_base_price = fields.Float(
        string="Gold/Silver Base Price (per gram)",
        compute='_compute_gold_silver_base_price', store=True
    )
    gold_silver_base_price_bhori = fields.Float(
        string="Gold/Silver Base Price (Per Bhori)",
        compute='_compute_gold_silver_base_price', store=True
    )
    labor_cost = fields.Float(string="Labor Cost")
    weight_in_grams = fields.Float(string="Weight (in grams)")
    hallmark = fields.Char(string="Hallmark (numeric)")
    certificate_name = fields.Char(string="Certificate Name") 
    
    weight_in_bhori = fields.Float(string="Weight (in bhori)", compute='_compute_weight_in_bhori', store=True)
    weight_in_bhori_only = fields.Integer(string="Bhori", compute='_compute_weight_in_bhori', store=True)
    weight_in_ana = fields.Integer(string="Ana", compute='_compute_weight_in_bhori', store=True)
    weight_in_rokti = fields.Integer(string="Rati", compute='_compute_weight_in_bhori', store=True)
    weight_in_point = fields.Integer(string="Point", compute='_compute_weight_in_bhori', store=True)
    
    final_sale_price = fields.Float(string="Final Sale Price", compute='_compute_final_sale_price', store=True)
    
    is_jewellery = fields.Boolean(string="Is Jewellery", default=True)

    @api.depends('product_karat')
    def _compute_gold_silver_base_price(self):
        latest_prices = self.env['gold.silver.prices'].search([], order='create_date desc', limit=1)
        
        for product in self:
            if not latest_prices:
                product.gold_silver_base_price = 0.0
                product.gold_silver_base_price_bhori = 0.0
                continue

            base_price = 0.0
            karat_code = product.product_karat
            price_field_name = config.PRICE_FIELD_MAP.get(karat_code)

            if price_field_name:
                base_price = getattr(latest_prices, price_field_name, 0.0)

            product.gold_silver_base_price = base_price
            product.gold_silver_base_price_bhori = base_price * config.GRAMS_PER_BHORI

    @api.depends('gold_silver_base_price', 'labor_cost', 'weight_in_grams')
    def _compute_final_sale_price(self):
        for product in self:
            if product.product_karat:
                base_price_total = product.gold_silver_base_price * product.weight_in_grams
                product_price_with_labor = base_price_total + product.labor_cost
                final_price = product_price_with_labor 
                product.list_price = final_price
                product.final_sale_price = final_price

    @api.depends('weight_in_grams')
    def _compute_weight_in_bhori(self):
        for product in self:
            if product.weight_in_grams:
                total_bhori = product.weight_in_grams / config.GRAMS_PER_BHORI
                
                bhori = math.floor(total_bhori)
                remainder_bhori = total_bhori - bhori
                
                ana_decimal = remainder_bhori * config.ANA_PER_BHORI
                ana = math.floor(ana_decimal)
                remainder_ana = ana_decimal - ana
                
                rokti_decimal = remainder_ana * config.ROKTI_PER_ANA
                rokti = math.floor(rokti_decimal)
                remainder_rokti = rokti_decimal - rokti
                
                point = round(remainder_rokti * config.POINT_PER_ROKTI)

                product.weight_in_bhori = total_bhori
                product.weight_in_bhori_only = bhori
                product.weight_in_ana = ana
                product.weight_in_rokti = rokti
                product.weight_in_point = point
            else:
                product.weight_in_bhori = 0.0
                product.weight_in_bhori_only = 0
                product.weight_in_ana = 0
                product.weight_in_rokti = 0
                product.weight_in_point = 0

    def _update_product_prices_scheduler(self):
        """Scheduler to update prices of all jewellery products."""
        products = self.search([('product_karat', '!=', False)])
        products._compute_gold_silver_base_price()
        products._compute_final_sale_price()
        return True
