import re

from odoo import api, fields, models

HOURS = ['%02d' % h for h in range(1, 25)]
HOUR_FIELDS = ['h%s' % h for h in HOURS]

# ---------------------------------------------------------------------------
# Row template: every row printed on the paper chart, in paper order.
# (code, section, label, kind, side_label)
#   section : nursing / vitals / resp  -> left grid of side 1
#             iv / output              -> right grid of side 1
#   kind    : input  -> nurse writes the cells
#             total  -> calculated by the system (running totals / balance)
# ---------------------------------------------------------------------------
ROW_TEMPLATE = [
    # ---- NURSING CARE ----
    ('apnoea', 'nursing', 'APNOEA/BRADYCARDIA', 'input', ''),
    ('colour', 'nursing', 'COLOUR', 'input', ''),
    ('resp_effort', 'nursing', 'RESPIRATORY EFFORT', 'input', ''),
    ('activity', 'nursing', 'ACTIVITY', 'input', ''),
    ('position', 'nursing', 'POSITION', 'input', ''),
    ('incubator_temp', 'nursing', 'INCUBATOR SET TEMP', 'input', ''),
    ('baby_temp', 'nursing', 'BABY TEMP/AIR TEMP', 'input', ''),
    ('temp_probe', 'nursing', 'TEMPERATURE PROBE*', 'input', '*RESITE'),
    # ---- VITAL SIGNS (plotted on the graph) ----
    ('hr', 'vitals', 'HR', 'input', 'Heart Rate'),
    ('rr', 'vitals', 'RR', 'input', 'Respiratory Rate'),
    ('bp', 'vitals', 'BP', 'input', 'Sys/Dia(Mean)'),
    ('temp', 'vitals', 'TEMP', 'input', 'Temperature'),
    # ---- VENTILATION / RESPIRATORY ----
    ('vent_mode', 'resp', 'VENTILATOR MODE', 'input', ''),
    ('rate', 'resp', 'RATE/FREQUENCY(HERTZ)', 'input', ''),
    ('insp_time', 'resp', 'INSPIRATORY TIME', 'input', ''),
    ('pip', 'resp', 'PIP/AMPLITUDE', 'input', ''),
    ('peep', 'resp', 'CPAP/PEEP', 'input', ''),
    ('map', 'resp', 'M.A.P', 'input', ''),
    ('ie_ratio', 'resp', 'IE RATIO', 'input', ''),
    ('fio2', 'resp', 'O2 CONC / BLENDED O2', 'input', ''),
    ('o2_flow', 'resp', 'O2 FLOW', 'input', ''),
    ('tcpo2_ino', 'resp', 'TCPO2/iNO', 'input', ''),
    ('spo2', 'resp', 'O2 SATURATION (PRE/POST)', 'input', '*RESITE'),
    ('probe_change', 'resp', 'PROBE CHANGE', 'input', ''),
    ('tcpo2_tcco2', 'resp', 'TCPO2/TCCO2', 'input', ''),
    ('ett_suction', 'resp', 'ETT SUCTION/AMOUNT', 'input', 'FREQUENCY'),
    ('suction_type', 'resp', 'TYPE', 'input', 'SUCTION CATH. SIZE'),
    ('opnp_suction', 'resp', 'OP/NP SUCTION', 'input', ''),
    ('air_entry', 'resp', 'AIR ENTRY L/R', 'input', 'Air entry = Equal / ↓ Decreased'),
    ('chest_physio', 'resp', 'CHEST PHYSIOTHERAPY', 'input', 'FREQUENCY'),
    ('sbr', 'resp', 'SBR', 'input', 'S-Single D-Double I-Intensive'),
    ('phototherapy', 'resp', 'PHOTOTHERAPY', 'input', ''),
    ('nursing_care', 'resp', 'GENERAL NURSING CARE', 'input', ''),
    ('pain', 'resp', 'PAIN SCORE', 'input', 'Please refer to pain tool'),
]

# IV / Medications / Blood products: 6 identical infusion blocks
for _i in range(1, 7):
    ROW_TEMPLATE += [
        ('iv%d_site' % _i, 'iv', 'SITE/IV check', 'input', ''),
        ('iv%d_pressure' % _i, 'iv', 'PRESSURE', 'input', ''),
        ('iv%d_hourly' % _i, 'iv', 'HOURLY (ml)', 'input', ''),
        ('iv%d_total' % _i, 'iv', 'TOTAL (ml)', 'total', ''),
    ]
ROW_TEMPLATE += [
    ('bolus_site', 'iv', 'SITE/IV check', 'input', ''),
    ('bolus_type', 'iv', 'BOLUS TYPE', 'input', ''),
    ('bolus_hourly', 'iv', 'HOURLY (ml)', 'input', ''),
    ('bolus_total', 'iv', 'TOTAL (ml)', 'total', ''),
    ('flush_arterial', 'iv', 'FLUSH ARTERIAL (ml)', 'input', ''),
    ('flush_drugs', 'iv', 'FLUSH DRUGS (ml)', 'input', ''),
    ('flush_total', 'iv', 'TOTAL (ml)', 'total', ''),
    ('bottling', 'iv', 'BOTTLING', 'input', 'Type / Strength'),
    ('feed_amount', 'iv', 'AMOUNT (ml)', 'input', 'Frequency / Increment'),
    ('feed_total', 'iv', 'TOTAL (ml)', 'total', ''),
    ('total_intake', 'iv', 'TOTAL INTAKE (ml/24h)', 'total', ''),
    # ---- OUTPUT ----
    ('glucose', 'output', 'BLOOD GLUCOSE', 'input', 'Frequency'),
    ('bowel_sounds', 'output', 'BOWEL SOUNDS P/A', 'input', 'Frequency'),
    ('girth', 'output', 'ABDOMINAL GIRTH', 'input', 'Frequency'),
    ('gastric', 'output', 'GASTRIC ASPIRATE (ml)', 'input', 'Frequency'),
    ('vomit', 'output', 'VOMIT (ml)', 'input', 'Measure'),
    ('ct_drain', 'output', 'CT DRAIN (ml) Right/Left', 'input', 'O-Oscillating / No Activity'),
    ('suction_pressure', 'output', 'SUCTION PRESSURE', 'input', ''),
    ('blood_loss', 'output', 'BLOOD LOSS (sample) (ml)', 'input', 'Measure'),
    ('urine', 'output', 'URINE (ml)', 'input', 'Measure'),
    ('urine_total', 'output', 'TOTAL URINE (ml)', 'total', ''),
    ('urine_rate', 'output', 'URINE OUTPUT (ml/kg/hr)', 'total', ''),
    ('stool', 'output', 'STOOL', 'input', 'Last stool (date)'),
    ('total_output', 'output', 'TOTAL OUTPUT (ml)', 'total', 'Measure'),
    ('fluid_balance', 'output', 'FLUID BALANCE (ml)', 'total', '24°'),
]

# Rows that count as intake / output for the running totals
INTAKE_CODES = ['iv%d_hourly' % i for i in range(1, 7)] + [
    'bolus_hourly', 'flush_arterial', 'flush_drugs', 'feed_amount']
OUTPUT_CODES = ['gastric', 'vomit', 'ct_drain', 'blood_loss', 'urine', 'stool']
# total row -> rows it accumulates
CUMULATIVE = {'iv%d_total' % i: ['iv%d_hourly' % i] for i in range(1, 7)}
CUMULATIVE.update({
    'bolus_total': ['bolus_hourly'],
    'flush_total': ['flush_arterial', 'flush_drugs'],
    'feed_total': ['feed_amount'],
    'total_intake': INTAKE_CODES,
    'urine_total': ['urine'],
    'total_output': OUTPUT_CODES,
})

_NUM_RE = re.compile(r'-?\d+(?:\.\d+)?')


def parse_number(value):
    """First number found in a cell ('2.4', '2.4ml', '10/12' -> 10). None if empty."""
    if not value:
        return None
    match = _NUM_RE.search(str(value).replace(',', '.'))
    return float(match.group()) if match else None


def parse_all_numbers(value):
    """All numbers in a cell: 'R5/L3' -> [5, 3] (used for CT drain right/left)."""
    if not value:
        return []
    return [float(n) for n in _NUM_RE.findall(str(value).replace(',', '.'))]


def fmt_number(value, digits=2):
    if value is None:
        return False
    value = round(value, digits)
    return ('%f' % value).rstrip('0').rstrip('.') or '0'


class NicuChartLine(models.Model):
    _name = 'nicu.chart.line'
    _description = 'NICU Chart Row (hourly)'
    _order = 'chart_id, sequence, id'

    chart_id = fields.Many2one('nicu.chart', required=True, ondelete='cascade', index=True)
    sequence = fields.Integer()
    code = fields.Char(required=True, readonly=True)
    section = fields.Selection([
        ('nursing', 'Nursing Care'),
        ('vitals', 'Vital Signs'),
        ('resp', 'Respiratory'),
        ('iv', 'IV / Medications / Blood Products'),
        ('output', 'Output'),
    ], required=True, readonly=True)
    name = fields.Char(string='Parameter', required=True, readonly=True)
    side_label = fields.Char(readonly=True)
    note = fields.Char(string='Note',
                       help='Free text written next to the row on the paper, e.g. the drug / fluid name '
                            'for an infusion block, frequency, feed type...')
    row_kind = fields.Selection([('input', 'Input'), ('total', 'Calculated')],
                                default='input', required=True, readonly=True)

    for _h in HOURS:
        locals()['h%s' % _h] = fields.Char(string=_h)
    del _h

    def values_list(self):
        self.ensure_one()
        return [self[f] or '' for f in HOUR_FIELDS]

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get('nicu_skip_recompute'):
            lines.chart_id._recompute_grid()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('nicu_skip_recompute') and (
                set(vals) & set(HOUR_FIELDS)):
            self.chart_id._recompute_grid()
        return res
