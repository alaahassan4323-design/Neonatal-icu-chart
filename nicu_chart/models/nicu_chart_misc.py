from odoo import api, fields, models

CATHETER_TYPES = [
    ('ett', 'ETT'),
    ('ngt', 'NGT/OGT'),
    ('np', 'NP'),
    ('uac', 'UAC'),
    ('uvc', 'UVC'),
    ('picc', 'PICC'),
    ('ict', 'ICT'),
]

# (name, label of 1st value, label of 2nd value)
SHIFT_CHECK_TEMPLATE = [
    ('Doctors Order Checked', '', ''),
    ('Medication Administration Record Checked', '', ''),
    ('IV/IA Fluids, Drugs Infusions, Rates, Sites (Including Heplocks)', '', ''),
    ('Resuscitation Equipment Checked: PPV Device, Mask, Suction Machine', '', ''),
    ('ID Bands On', 'Infant', 'Cot'),
    ('Monitor/Alarms/Limits', '', ''),
    ('Nursing Care Plan Revision & Update', '', ''),
    ('Transducer Calibrated', '', ''),
    ('Tracheal Aspirate – Done', 'Done', 'Due'),
    ('Central Line Dressing – Done', 'Done', 'Due'),
    ('Phototherapy Lights / Eye Pads', '', ''),
    ('Ventilator Changed (Date)', 'Date', 'Due'),
    ('Incubator Changed (Date)', 'Date', 'Due'),
    ('Humidity Changed Daily', '', 'Time'),
]


class NicuChartCatheter(models.Model):
    _name = 'nicu.chart.catheter'
    _description = 'NICU Chart Catheter / Line'
    _order = 'chart_id, sequence, id'

    chart_id = fields.Many2one('nicu.chart', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer()
    catheter_type = fields.Selection(CATHETER_TYPES, string='Catheter', required=True)
    size = fields.Char()
    level = fields.Char()
    insertion_date = fields.Date(string='Insertion Date')
    duration = fields.Char(compute='_compute_duration', string='Duration')
    type_label = fields.Char(compute='_compute_type_label')

    def _compute_type_label(self):
        labels = dict(CATHETER_TYPES)
        for line in self:
            line.type_label = labels.get(line.catheter_type, '')

    @api.depends('insertion_date', 'chart_id.date')
    def _compute_duration(self):
        for line in self:
            if line.insertion_date and line.chart_id.date:
                days = (line.chart_id.date - line.insertion_date).days
                line.duration = 'Day %d' % (days + 1) if days >= 0 else False
            else:
                line.duration = False


class NicuChartShiftCheck(models.Model):
    _name = 'nicu.chart.shift.check'
    _description = 'NICU Chart Shift Check'
    _order = 'chart_id, sequence, id'

    chart_id = fields.Many2one('nicu.chart', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer()
    day_check = fields.Char(string='Day')
    name = fields.Char(string='Shift Check', required=True, readonly=True)
    label1 = fields.Char(readonly=True)
    value1 = fields.Char(string='Value')
    label2 = fields.Char(readonly=True)
    value2 = fields.Char(string='Value 2')
    night_check = fields.Char(string='Night')


class NicuChartNote(models.Model):
    _name = 'nicu.chart.note'
    _description = 'NICU Chart Progress Evaluation'
    _order = 'chart_id, date, time, id'

    def _default_time(self):
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        return now.strftime('%H%M') + 'H'

    chart_id = fields.Many2one('nicu.chart', required=True, ondelete='cascade', index=True)
    date = fields.Date(default=fields.Date.context_today, required=True)
    time = fields.Char(default=_default_time)
    note = fields.Text(string='Progress Evaluation', required=True)
    nurse_id = fields.Many2one('res.users', string='Nurse', default=lambda self: self.env.user)
    signature = fields.Char(string="Nurse's Signature",
                            default=lambda self: self.env.user.name)
