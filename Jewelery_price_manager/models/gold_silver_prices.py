# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import math
import base64
import csv
import io
from odoo.exceptions import UserError

class GoldSilverPrices(models.Model):
    _name = 'gold.silver.prices'
    _description = 'Gold and Silver Prices'

    name = fields.Char(string="Record Title", required=True)
    
    # Gold prices
    gold_22k_price = fields.Float(string="22K Gold Price (per gram)")
    gold_21k_price = fields.Float(string="21K Gold Price (per gram)")
    gold_18k_price = fields.Float(string="18K Gold Price (per gram)")
    gold_traditional_price = fields.Float(string="Traditional Gold Price (per gram)")

    # Silver prices
    silver_22k_price = fields.Float(string="22K Silver Price (per gram)")
    silver_21k_price = fields.Float(string="21K Silver Price (per gram)")
    silver_18k_price = fields.Float(string="18K Silver Price (per gram)")
    silver_traditional_price = fields.Float(string="Traditional Silver Price (per gram)")
    silver_italian_price = fields.Float(string="Italian Silver Price (per gram)")
    
    def manual_update_prices(self):
        """Action to manually update all product prices based on current rates."""
        self.ensure_one()
        self.env['product.template']._update_product_prices_scheduler()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success!"),
                'message': _("All product prices have been successfully updated."),
                'type': 'success',
                'sticky': False,
            }
        }