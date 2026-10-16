from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_nicu_patient = fields.Boolean(string='NICU Patient')
    nicu_mrn = fields.Char(string='MRN', index=True)
    nicu_birth_date = fields.Date(string='Date of Birth')
    nicu_ga_weeks = fields.Integer(string='Gestational Age (weeks)')
    nicu_ga_days = fields.Integer(string='Gestational Age (days)')
    nicu_birth_weight = fields.Float(string='Birth Weight (g)')
    nicu_blood_group = fields.Char(string='Blood Group')
    nicu_chart_ids = fields.One2many('nicu.chart', 'patient_id', string='NICU Charts')
    nicu_chart_count = fields.Integer(compute='_compute_nicu_chart_count')

    def _compute_nicu_chart_count(self):
        for partner in self:
            partner.nicu_chart_count = len(partner.nicu_chart_ids)

    def action_view_nicu_charts(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('nicu_chart.action_nicu_chart')
        action['domain'] = [('patient_id', '=', self.id)]
        action['context'] = {'default_patient_id': self.id}
        return action
