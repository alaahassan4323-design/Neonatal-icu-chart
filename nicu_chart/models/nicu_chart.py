from datetime import timedelta

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from .assessment_spec import ASSESSMENT_COLUMNS, ASSESSMENT_FOOTER, SHIFTS, iter_assessment_items
from .nicu_chart_line import (
    CUMULATIVE, HOUR_FIELDS, HOURS, INTAKE_CODES, OUTPUT_CODES, ROW_TEMPLATE,
    fmt_number, parse_all_numbers, parse_number,
)
from .nicu_chart_misc import CATHETER_TYPES, SHIFT_CHECK_TEMPLATE

# Codes whose cell may hold several numbers that must be added (CT drain R/L)
MULTI_VALUE_CODES = {'ct_drain'}

# Header fields carried over to the next day's chart
CARRY_OVER_FIELDS = [
    'diagnosis', 'consultant', 'nte_range',
    'hr_alarm_low', 'hr_alarm_high', 'rr_alarm_low', 'rr_alarm_high',
    'spo2_alarm_low', 'spo2_alarm_high', 'mean_bp_alarm',
    'blood_gas_type', 'gas_ph', 'gas_pco2', 'gas_po2', 'gas_hco3',
    'other_instructions', 'head_circumference', 'tfi_ml_kg_day',
    'tpn_ml_hr', 'intralipids_ml_hr', 'amended_tf', 'parent_last_visit',
]


class NicuChart(models.Model):
    _name = 'nicu.chart'
    _description = 'Neonatal ICU Chart'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)

    # ------------------------------------------------------------------
    # PATIENT I.D.
    # ------------------------------------------------------------------
    patient_id = fields.Many2one('res.partner', string='Name', required=True, tracking=True,
                                 domain=[('is_nicu_patient', '=', True)], index=True)
    mrn = fields.Char(related='patient_id.nicu_mrn', readonly=False, string='MRN')
    diagnosis = fields.Char()
    consultant = fields.Char()
    date_of_birth = fields.Date(related='patient_id.nicu_birth_date', readonly=False)
    age_days = fields.Integer(string='Age in days', compute='_compute_ages')
    ga_weeks = fields.Integer(related='patient_id.nicu_ga_weeks', readonly=False,
                              string='Gestational age (weeks)')
    ga_days = fields.Integer(related='patient_id.nicu_ga_days', readonly=False,
                             string='Gestational age (days)')
    corrected_age = fields.Char(compute='_compute_ages')
    birth_weight = fields.Float(related='patient_id.nicu_birth_weight', readonly=False,
                                string='Birth weight (g)')
    present_weight = fields.Float(string='Present weight (g)', tracking=True)
    previous_weight = fields.Float(string='Previous weight (g)')
    weight_change = fields.Char(string='Change', compute='_compute_weight_change')
    head_circumference = fields.Float(string='Head circumference (cm)')
    blood_group = fields.Char(related='patient_id.nicu_blood_group', readonly=False)
    parent_last_visit = fields.Date(string='Parent last visit')
    ebm_given = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='EBM given')
    ebm_ml = fields.Float(string='EBM (ml)')

    # TOTAL FLUID INTAKE
    tfi_ml_kg_day = fields.Float(string='ml/kg/day')
    tfi_ml_hr = fields.Float(string='ml/hr', compute='_compute_tfi_ml_hr', store=True,
                             readonly=False)
    tpn_ml_hr = fields.Char(string='TPN (ml/hr)')
    intralipids_ml_hr = fields.Char(string='Intralipids (ml/hr)')
    amended_tf = fields.Char(string='Amended T.F.')

    # 24 HOUR SUMMARY (calculated from the IV / output grid)
    total_actual_intake = fields.Float(string='Total actual intake (ml)', readonly=True)
    total_output = fields.Float(string='Total output (ml)', readonly=True)
    urine_output_rate = fields.Float(string='Urine output (ml/kg/hr)', readonly=True)
    fluid_balance = fields.Float(string='Fluid balance (ml)', readonly=True)
    total_blood_loss = fields.Float(string='Total blood loss (ml)', readonly=True)
    investigations = fields.Text()

    # ------------------------------------------------------------------
    # LEFT PANEL (side 1)
    # ------------------------------------------------------------------
    nte_range = fields.Char(string='NTE Range')
    hr_alarm_low = fields.Char(string='Heart rate (low)')
    hr_alarm_high = fields.Char(string='Heart rate (high)')
    rr_alarm_low = fields.Char(string='Resp. rate (low)')
    rr_alarm_high = fields.Char(string='Resp. rate (high)')
    spo2_alarm_low = fields.Char(string='O2 saturation (low)')
    spo2_alarm_high = fields.Char(string='O2 saturation (high)')
    mean_bp_alarm = fields.Char(string='Mean BP')
    blood_gas_type = fields.Selection([
        ('arterial', 'Arterial'), ('venous', 'Venous'), ('capillary', 'Capillary')],
        string='Blood gas')
    gas_ph = fields.Char(string='pH')
    gas_pco2 = fields.Char(string='pCO2')
    gas_po2 = fields.Char(string='pO2')
    gas_hco3 = fields.Char(string='HCO3')
    other_instructions = fields.Text()

    # ------------------------------------------------------------------
    # GRIDS
    # ------------------------------------------------------------------
    line_ids = fields.One2many('nicu.chart.line', 'chart_id', string='All rows')
    nursing_line_ids = fields.One2many('nicu.chart.line', 'chart_id',
                                       domain=[('section', '=', 'nursing')], string='Nursing Care')
    vitals_line_ids = fields.One2many('nicu.chart.line', 'chart_id',
                                      domain=[('section', '=', 'vitals')], string='Vital Signs')
    resp_line_ids = fields.One2many('nicu.chart.line', 'chart_id',
                                    domain=[('section', '=', 'resp')], string='Respiratory')
    iv_line_ids = fields.One2many('nicu.chart.line', 'chart_id',
                                  domain=[('section', '=', 'iv')],
                                  string='IV / Medications / Blood Products')
    output_line_ids = fields.One2many('nicu.chart.line', 'chart_id',
                                      domain=[('section', '=', 'output')], string='Output')
    catheter_ids = fields.One2many('nicu.chart.catheter', 'chart_id', string='Catheters')
    vitals_graph = fields.Html(compute='_compute_vitals_graph', sanitize=False)

    # ------------------------------------------------------------------
    # SIDE 2
    # ------------------------------------------------------------------
    shift_check_ids = fields.One2many('nicu.chart.shift.check', 'chart_id', string='Shift Check')
    special_instructions = fields.Text()
    note_ids = fields.One2many('nicu.chart.note', 'chart_id', string='Progress Evaluation')

    # Physical assessment: day_* and night_* fields generated from the spec
    for _shift, _shift_label in SHIFTS:
        for _key, _label, _type in iter_assessment_items():
            _fname = '%s_%s' % (_shift, _key)
            _string = '%s - %s' % (_shift_label.title(), _label)
            if _type == 'bool':
                locals()[_fname] = fields.Boolean(string=_string)
            elif _type == 'date':
                locals()[_fname] = fields.Date(string=_string)
            elif _type == 'text':
                locals()[_fname] = fields.Text(string=_string)
            else:
                locals()[_fname] = fields.Char(string=_string)
    del _shift, _shift_label, _key, _label, _type, _fname, _string

    # ------------------------------------------------------------------
    # COMPUTES
    # ------------------------------------------------------------------
    @api.depends('patient_id.name', 'date')
    def _compute_name(self):
        for chart in self:
            parts = [chart.patient_id.name or _('New'), fields.Date.to_string(chart.date) or '']
            chart.name = ' - '.join(p for p in parts if p)

    @api.depends('date', 'date_of_birth', 'ga_weeks', 'ga_days')
    def _compute_ages(self):
        for chart in self:
            age = False
            corrected = False
            if chart.date and chart.date_of_birth:
                age = (chart.date - chart.date_of_birth).days
                if chart.ga_weeks:
                    total = chart.ga_weeks * 7 + (chart.ga_days or 0) + age
                    corrected = _('%(w)s weeks + %(d)s days', w=total // 7, d=total % 7)
            chart.age_days = age
            chart.corrected_age = corrected

    @api.depends('present_weight', 'previous_weight')
    def _compute_weight_change(self):
        for chart in self:
            if chart.present_weight and chart.previous_weight:
                diff = chart.present_weight - chart.previous_weight
                if diff > 0:
                    chart.weight_change = _('%s gram increased', fmt_number(diff))
                elif diff < 0:
                    chart.weight_change = _('%s gram decreased', fmt_number(-diff))
                else:
                    chart.weight_change = _('No change')
            else:
                chart.weight_change = False

    def _weight_kg(self):
        self.ensure_one()
        grams = self.present_weight or self.birth_weight
        return grams / 1000.0 if grams else 0.0

    @api.depends('tfi_ml_kg_day', 'present_weight', 'birth_weight')
    def _compute_tfi_ml_hr(self):
        for chart in self:
            kg = chart._weight_kg()
            chart.tfi_ml_hr = round(chart.tfi_ml_kg_day * kg / 24.0, 2) if kg else 0.0

    @api.depends(*['vitals_line_ids.%s' % f for f in HOUR_FIELDS])
    def _compute_vitals_graph(self):
        for chart in self:
            rows = {line.code: line.values_list() for line in chart.vitals_line_ids}
            chart.vitals_graph = chart._build_vitals_svg(rows)

    # ------------------------------------------------------------------
    # CONSTRAINTS / ONCHANGE
    # ------------------------------------------------------------------
    @api.constrains('patient_id', 'date')
    def _check_unique_chart(self):
        for chart in self:
            if self.search_count([('patient_id', '=', chart.patient_id.id),
                                  ('date', '=', chart.date), ('id', '!=', chart.id)]):
                raise ValidationError(_('This patient already has a chart for %s.', chart.date))

    def _previous_chart(self):
        self.ensure_one()
        if not self.patient_id or not self.date:
            return self.browse()
        domain = [('patient_id', '=', self.patient_id.id), ('date', '<', self.date)]
        if self.id and isinstance(self.id, int):
            domain.append(('id', '!=', self.id))
        return self.search(domain, order='date desc', limit=1)

    @api.onchange('patient_id', 'date')
    def _onchange_patient_date(self):
        previous = self._previous_chart()
        if previous:
            if not self.previous_weight:
                weighed = self.search([('patient_id', '=', self.patient_id.id), ('date', '<', self.date),
                                       ('present_weight', '>', 0)], order='date desc', limit=1)
                self.previous_weight = weighed.present_weight
            for fname in ('diagnosis', 'consultant', 'head_circumference', 'tfi_ml_kg_day'):
                if not self[fname]:
                    self[fname] = previous[fname]

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        charts = super().create(vals_list)
        for chart in charts:
            chart._init_template_rows()
        charts._recompute_grid()
        return charts

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('nicu_skip_recompute') and (
                {'present_weight', 'patient_id'} & set(vals)):
            self._recompute_grid()
        return res

    def _init_template_rows(self):
        self.ensure_one()
        ctx = dict(self.env.context, nicu_skip_recompute=True)
        existing = set(self.line_ids.mapped('code'))
        self.env['nicu.chart.line'].with_context(ctx).create([{
            'chart_id': self.id,
            'sequence': seq,
            'code': code,
            'section': section,
            'name': label,
            'row_kind': kind,
            'side_label': side,
        } for seq, (code, section, label, kind, side) in enumerate(ROW_TEMPLATE)
            if code not in existing])
        if not self.catheter_ids:
            self.env['nicu.chart.catheter'].create([{
                'chart_id': self.id, 'sequence': seq, 'catheter_type': key,
            } for seq, (key, _label) in enumerate(CATHETER_TYPES)])
        if not self.shift_check_ids:
            self.env['nicu.chart.shift.check'].create([{
                'chart_id': self.id, 'sequence': seq, 'name': name,
                'label1': label1, 'label2': label2,
            } for seq, (name, label1, label2) in enumerate(SHIFT_CHECK_TEMPLATE)])

    # ------------------------------------------------------------------
    # CALCULATIONS: running totals, urine output, fluid balance, 24h summary
    # ------------------------------------------------------------------
    def _recompute_grid(self):
        Line = self.env['nicu.chart.line'].with_context(nicu_skip_recompute=True)
        for chart in self:
            lines = {line.code: line for line in chart.line_ids}
            if not lines:
                continue

            def series(code):
                line = lines.get(code)
                if not line:
                    return [None] * 24
                if code in MULTI_VALUE_CODES:
                    return [sum(parse_all_numbers(v)) if parse_all_numbers(v) else None
                            for v in line.values_list()]
                return [parse_number(v) for v in line.values_list()]

            cache = {code: series(code) for code in set(INTAKE_CODES + OUTPUT_CODES + ['urine'])}

            def cumulative(codes):
                result, running, seen = [], 0.0, False
                for k in range(24):
                    for code in codes:
                        value = cache[code][k]
                        if value is not None:
                            running += value
                            seen = True
                    result.append(running if seen else None)
                return result

            # last hour that has any intake/output written
            last = -1
            for values in cache.values():
                for k, value in enumerate(values):
                    if value is not None:
                        last = max(last, k)

            computed = {}
            for code, sources in CUMULATIVE.items():
                cum = cumulative(sources)
                computed[code] = [v if k <= last else None for k, v in enumerate(cum)]

            kg = chart._weight_kg()
            urine_cum = computed['urine_total']
            computed['urine_rate'] = [
                (urine_cum[k] / kg / (k + 1)) if (urine_cum[k] is not None and kg) else None
                for k in range(24)]
            intake_cum = computed['total_intake']
            output_cum = computed['total_output']
            computed['fluid_balance'] = [
                ((intake_cum[k] or 0.0) - (output_cum[k] or 0.0))
                if (intake_cum[k] is not None or output_cum[k] is not None) else None
                for k in range(24)]

            for code, values in computed.items():
                line = lines.get(code)
                if not line:
                    continue
                vals = {}
                digits = 2 if code == 'urine_rate' else 1
                for fname, value in zip(HOUR_FIELDS, values):
                    new = fmt_number(value, digits)
                    if (line[fname] or False) != new:
                        vals[fname] = new
                if vals:
                    Line.browse(line.id).write(vals)

            def final(values):
                return values[last] if last >= 0 and values[last] is not None else 0.0

            blood_loss_cum = cumulative(['blood_loss'])
            hours = last + 1 if last >= 0 else 0
            chart.with_context(nicu_skip_recompute=True).write({
                'total_actual_intake': round(final(intake_cum), 2),
                'total_output': round(final(output_cum), 2),
                'urine_output_rate': round(final(urine_cum) / kg / hours, 2) if (kg and hours) else 0.0,
                'fluid_balance': round(final(computed['fluid_balance']), 2),
                'total_blood_loss': round(final(blood_loss_cum), 2),
            })

    def action_recompute(self):
        self._recompute_grid()
        return True

    # ------------------------------------------------------------------
    # ACTIONS
    # ------------------------------------------------------------------
    def action_next_day_chart(self):
        """Open (or create) tomorrow's chart, carrying over the header,
        catheters and the names written on the IV blocks."""
        self.ensure_one()
        next_date = self.date + timedelta(days=1)
        chart = self.search([('patient_id', '=', self.patient_id.id), ('date', '=', next_date)], limit=1)
        if not chart:
            vals = {fname: self[fname] for fname in CARRY_OVER_FIELDS}
            vals.update({
                'patient_id': self.patient_id.id,
                'date': next_date,
                'previous_weight': self.present_weight,
            })
            chart = self.create(vals)
            notes = {line.code: line.note for line in self.line_ids if line.note}
            for line in chart.line_ids:
                if line.code in notes:
                    line.note = notes[line.code]
            old_cath = {c.catheter_type: c for c in self.catheter_ids}
            for cath in chart.catheter_ids:
                src = old_cath.get(cath.catheter_type)
                if src:
                    cath.write({'size': src.size, 'level': src.level,
                                'insertion_date': src.insertion_date})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nicu.chart',
            'res_id': chart.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_print_chart(self):
        return self.env.ref('nicu_chart.action_report_nicu_chart').report_action(self)

    # ------------------------------------------------------------------
    # REPORT HELPERS
    # ------------------------------------------------------------------
    def get_rows(self, section):
        self.ensure_one()
        return self.line_ids.filtered(lambda l: l.section == section).sorted('sequence')

    def get_report_graph(self):
        self.ensure_one()
        rows = {line.code: line.values_list() for line in self.vitals_line_ids}
        return self._build_vitals_svg(rows, for_report=True)

    def get_assessment_columns(self):
        return ASSESSMENT_COLUMNS

    def get_assessment_footer(self):
        return ASSESSMENT_FOOTER[1:]

    def get_note_columns(self, rows_per_column=80, chars_per_line=120):
        """Split progress notes over the two ruled columns of side 2 and pad
        each column with empty ruled lines like the paper."""
        self.ensure_one()
        notes = self.note_ids.sorted(lambda n: (n.date or fields.Date.today(), n.time or '', n.id))

        def height(note):
            text = note.note or ''
            return max(1, sum(max(1, -(-len(part) // chars_per_line)) for part in text.split('\n')))

        total = sum(height(n) for n in notes)
        first, second, used = [], [], 0
        for note in notes:
            target = first if used < rows_per_column else second
            target.append(note)
            if target is first:
                used += height(note)
        pad1 = max(0, rows_per_column - sum(height(n) for n in first))
        pad2 = max(0, rows_per_column - sum(height(n) for n in second))
        return [(first, pad1), (second, pad2)]

    def get_hours(self):
        return HOURS

    def get_hour_fields(self):
        return HOUR_FIELDS

    def get_iv_blocks(self):
        """IV section grouped in blocks the way the paper groups them."""
        self.ensure_one()
        rows = self.get_rows('iv')
        blocks, current = [], []
        starts = ('_site', 'flush_arterial', 'bottling', 'total_intake')
        for row in rows:
            if current and (row.code.endswith('_site') or row.code in starts):
                blocks.append(current)
                current = []
            current.append(row)
        if current:
            blocks.append(current)
        return blocks

    # ------------------------------------------------------------------
    # VITAL SIGNS GRAPH (same scales as the paper)
    # ------------------------------------------------------------------
    @api.model
    def _build_vitals_svg(self, rows, for_report=False):
        # In the report the proportions follow the printed columns
        # (label column 28mm / hour column 5.8mm) so the hours line up.
        label_w, col_w, row_h, n_rows = (164, 34, 34, 10) if for_report else (112, 34, 26, 10)
        top = 22
        width = label_w + 24 * col_w
        height = top + n_rows * row_h + 6
        scales = [
            ('HR', 220, 20), ('RR', 100, 10), ('BP', 110, 10),
        ]
        temp_labels = ['PR', 'PA', '42', '40', '38', '36', '34', '32', '30', '28']

        def y_for(kind, value):
            if kind == 'TEMP':
                idx = 2 + (42.0 - value) / 2.0
            else:
                start, step = {s[0]: (s[1], s[2]) for s in scales}[kind]
                idx = (start - value) / float(step)
            idx = max(0.0, min(n_rows - 1.0, idx))
            return top + row_h / 2.0 + idx * row_h

        def x_for(k):
            return label_w + k * col_w + col_w / 2.0

        out = [
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" '
            'width="100%%" preserveAspectRatio="xMinYMin meet" '
            'style="font-family:Arial,Helvetica,sans-serif;font-size:10px;background:#fff">' % (width, height)
        ]
        # header
        out.append('<rect x="0" y="0" width="%d" height="%d" fill="#d9d9d9" stroke="#555"/>' % (width, top))
        sub_w = label_w / 4.0
        for i, title in enumerate(['HR', 'RR', 'BP', 'TEMP']):
            out.append('<text x="%.1f" y="15" text-anchor="middle" font-weight="bold">%s</text>'
                       % (i * sub_w + sub_w / 2, title))
        for k, hour in enumerate(HOURS):
            out.append('<text x="%.1f" y="15" text-anchor="middle" font-weight="bold">%sH</text>'
                       % (x_for(k), hour))
        # grid
        for r in range(n_rows):
            y = top + r * row_h
            out.append('<rect x="0" y="%d" width="%d" height="%d" fill="none" stroke="#999" stroke-width="0.6"/>'
                       % (y, width, row_h))
            labels = [str(220 - r * 20), str(100 - r * 10), str(110 - r * 10), temp_labels[r]]
            for i, lab in enumerate(labels):
                out.append('<text x="%.1f" y="%.1f" text-anchor="middle">%s</text>'
                           % (i * sub_w + sub_w / 2, y + row_h / 2.0 + 3.5, lab))
        for i in range(1, 4):
            out.append('<line x1="%.1f" y1="0" x2="%.1f" y2="%d" stroke="#999" stroke-width="0.6"/>'
                       % (i * sub_w, i * sub_w, height - 6))
        for k in range(25):
            x = label_w + k * col_w
            out.append('<line x1="%d" y1="0" x2="%d" y2="%d" stroke="#999" stroke-width="0.6"/>'
                       % (x, x, height - 6))

        def points(code, kind):
            pts = []
            for k, raw in enumerate(rows.get(code, [''] * 24)):
                value = parse_number(raw)
                if value is not None:
                    pts.append((x_for(k), y_for(kind, value), raw))
            return pts

        # Heart rate: red dots joined by a line
        hr = points('hr', 'HR')
        if len(hr) > 1:
            out.append('<polyline fill="none" stroke="#c0392b" stroke-width="1.4" points="%s"/>'
                       % ' '.join('%.1f,%.1f' % (x, y) for x, y, _r in hr))
        for x, y, raw in hr:
            out.append('<circle cx="%.1f" cy="%.1f" r="3" fill="#c0392b"/>' % (x, y))
            if for_report:
                out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="8" fill="#c0392b">%s</text>'
                           % (x, y - 5, escape(raw)))
        # Respiratory rate: black dots, dashed line
        rr = points('rr', 'RR')
        if len(rr) > 1:
            out.append('<polyline fill="none" stroke="#222" stroke-width="1" stroke-dasharray="3,2" points="%s"/>'
                       % ' '.join('%.1f,%.1f' % (x, y) for x, y, _r in rr))
        for x, y, raw in rr:
            out.append('<circle cx="%.1f" cy="%.1f" r="2.4" fill="#222"/>' % (x, y))
            if for_report:
                out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="8">%s</text>'
                           % (x, y + 11, escape(raw)))
        # Temperature: squares
        for x, y, raw in points('temp', 'TEMP'):
            out.append('<rect x="%.1f" y="%.1f" width="6" height="6" fill="#1f5fa8"/>' % (x - 3, y - 3))
            if for_report:
                out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="8" fill="#1f5fa8">%s</text>'
                           % (x, y - 6, escape(raw)))
        # Blood pressure: vertical bar systolic -> diastolic, mean in brackets
        for k, raw in enumerate(rows.get('bp', [''] * 24)):
            nums = parse_all_numbers(raw)
            if len(nums) >= 2:
                x = x_for(k)
                y1, y2 = y_for('BP', nums[0]), y_for('BP', nums[1])
                out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="#555" stroke-width="1.4"/>'
                           % (x, y1, x, y2))
                out.append('<path d="M%.1f %.1f l-3 5 h6 z" fill="#555"/>' % (x, y1))
                out.append('<path d="M%.1f %.1f l-3 -5 h6 z" fill="#555"/>' % (x, y2))
                if len(nums) >= 3:
                    out.append('<text x="%.1f" y="%.1f" text-anchor="middle" font-size="8">(%s)</text>'
                               % (x + 9, (y1 + y2) / 2.0 + 3, fmt_number(nums[2])))
        out.append('</svg>')
        return Markup(''.join(out))
