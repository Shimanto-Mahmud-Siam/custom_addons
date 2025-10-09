# -*- coding: utf-8 -*-

from odoo import api, fields, models
import random
import logging

_logger = logging.getLogger(__name__)

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    barcode = fields.Char('Barcode')

    @api.model
    def create(self, vals):
        """
        Overrides the default create method for product.template.
        Generates a unique barcode if one is not provided.
        """
        if not vals.get('barcode'):
            vals['barcode'] = self._get_unique_barcode()
        
        return super(ProductTemplate, self).create(vals)

    def _get_unique_barcode(self):
        """
        Generates and returns a unique 13-digit barcode.
        """
        while True:
            new_barcode = str(random.randint(1000000000000, 9999999999999))
            
            # Check for uniqueness across product templates and variants
            existing_product = self.env['product.template'].search([('barcode', '=', new_barcode)], limit=1)
            existing_variant = self.env['product.product'].search([('barcode', '=', new_barcode)], limit=1)

            if not existing_product and not existing_variant:
                _logger.info(f"Generated new unique barcode: {new_barcode}")
                return new_barcode

    def action_generate_barcode(self):
        """
        Button action to manually generate a new unique barcode.
        """
        for product in self:
            product.barcode = self._get_unique_barcode()