from odoo import models, fields


class Product_Template(models.Model):
    _inherit = 'product.template'

    ma_labs_list = fields.Char(string='Ma Labs List #')
    item = fields.Char(string='Item #')
    mfr_part = fields.Char(string='Mfr Part #')
    manufacturer = fields.Char(string='Manufacturer')
    package = fields.Char(string='Package')
    unit = fields.Char(string='Unit')
    website_description = fields.Html(string='Website Description')
    instant_rebate = fields.Float(string='Instant Rebate')
    instant_rebate_start = fields.Char(string='Instant Rebate Start')
    instant_rebate_end = fields.Char(string='Instant Rebate End')
    usd_sales_price = fields.Float(string='USD - Sales Price')
    usd_cost = fields.Float(string='USD - Cost')
    width_cm = fields.Char(string='Width (cm)')
    height_cm = fields.Char(string='Height (cm)')
    length_cm = fields.Char(string='Length (cm)')
    descript = fields.Char(string='Descript')
    upc_code = fields.Char(string='UPC Code')

