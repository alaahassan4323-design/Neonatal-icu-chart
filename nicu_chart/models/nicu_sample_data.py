"""Sample (demo) data: one baby with a fully filled 24-hour chart, modelled on
a real paper chart (values only, no real patient identity)."""
from datetime import timedelta

from odoo import api, fields, models

from .nicu_chart_line import HOURS

SAMPLE_MRN = 'DEMO-0001'


def _every(step, value, start=1):
    """{hour: value} every `step` hours starting at `start`."""
    return {h: (value(h) if callable(value) else value) for h in range(start, 25, step)}


HR = [148, 150, 143, 150, 152, 143, 148, 158, 154, 146, 142, 140, 147, 143, 153, 153, 149, 144,
      156, 143, 157, 142, 152, 157]
RR = [52, 48, 50, 46, 54, 50, 47, 45, 48, 50, 52, 49, 51, 47, 45, 50, 48, 46, 49, 51, 50, 47, 49, 52]
POSITIONS = ['S', 'S', 'S', 'LL', 'LL', 'LL', 'P', 'P', 'P', 'RL', 'RL', 'RL']
ACTIVITY = ['QS', 'QS', 'AS', 'QA', 'QS', 'QS', 'AA', 'QA', 'QS', 'AS', 'QS', 'QS']


def _sample_grid():
    g = {}
    # ---- nursing care
    g['apnoea'] = _every(1, '0/0')
    g['apnoea'][16] = '1/0'
    g['colour'] = _every(1, 'P')
    g['resp_effort'] = _every(1, lambda h: 'E' if h % 4 else 'IC/M')
    g['activity'] = _every(1, lambda h: ACTIVITY[(h - 1) % 12])
    g['position'] = _every(1, lambda h: POSITIONS[(h - 1) // 2 % 12])
    g['incubator_temp'] = _every(1, '36.5')
    g['baby_temp'] = _every(3, lambda h: '36.%d/34' % (5 + h % 4))
    g['temp_probe'] = _every(12, '*')
    # ---- vital signs (graph)
    g['hr'] = {h: str(HR[h - 1]) for h in range(1, 25)}
    g['rr'] = {h: str(RR[h - 1]) for h in range(1, 25)}
    g['bp'] = _every(3, lambda h: '%d/%d(%d)' % (58 + h % 5, 33 + h % 3, 44 + h % 3))
    g['temp'] = _every(3, lambda h: '36.%d' % (5 + h % 4))
    # ---- ventilation
    g['vent_mode'] = _every(1, 'PC-PSV')
    g['rate'] = _every(1, lambda h: '35' if h < 9 else '30')
    g['insp_time'] = _every(1, '0.35')
    g['pip'] = _every(1, lambda h: '18' if h < 13 else '16')
    g['peep'] = _every(1, '6')
    g['map'] = _every(1, lambda h: '8.2' if h < 13 else '7.8')
    g['ie_ratio'] = _every(1, '1:1.5')
    g['fio2'] = _every(1, lambda h: '25' if h < 9 or h > 18 else '23')
    g['o2_flow'] = _every(1, '8')
    g['spo2'] = _every(1, lambda h: '%d/%d' % (92 + h % 3, 94 + h % 3))
    g['spo2'][16] = '82/85'
    g['probe_change'] = _every(3, '✓')
    g['ett_suction'] = _every(6, 'S/CL', start=3)
    g['suction_type'] = _every(6, 'Closed 6Fr', start=3)
    g['opnp_suction'] = _every(6, 'SC/CL', start=3)
    g['air_entry'] = _every(3, '=')
    g['nursing_care'] = _every(3, '✓')
    g['pain'] = _every(3, '0')
    # ---- IV / medications
    for h in range(1, 25):
        h_ = h
        g.setdefault('iv1_site', {})[h_] = '✓'
        g.setdefault('iv1_pressure', {})[h_] = str(24 + h % 4)
        g.setdefault('iv1_hourly', {})[h_] = '4.3'
        g.setdefault('iv2_site', {})[h_] = '✓'
        g.setdefault('iv2_pressure', {})[h_] = str(25 + h % 3)
        g.setdefault('iv2_hourly', {})[h_] = '0.37'
    g['iv3_site'] = {10: '✓', 22: '✓'}
    g['iv3_hourly'] = {10: '0.2', 22: '0.2'}
    g['flush_drugs'] = {10: '0.5', 22: '0.5'}
    g['bottling'] = {1: 'NPO'}
    # ---- output
    g['glucose'] = {6: '5.8', 12: '4.9', 18: '5.2', 24: '6.1'}
    g['bowel_sounds'] = _every(6, 'P', start=6)
    g['girth'] = {6: '22.5', 18: '22.5'}
    g['gastric'] = _every(6, 'Nil', start=6)
    g['blood_loss'] = {4: '0.5', 16: '0.3'}
    urine = [12, 15, 10, 18, 14, 16, 11, 13]
    g['urine'] = {h: str(urine[i]) for i, h in enumerate(range(3, 25, 3))}
    g['stool'] = {9: 'Nil', 21: 'Nil'}
    return g


class NicuChart(models.Model):
    _inherit = 'nicu.chart'

    @api.model
    def _create_sample_data(self):
        """Create (once) a demo baby with yesterday's and today's chart."""
        Partner = self.env['res.partner']
        today = fields.Date.context_today(self)
        patient = Partner.search([('nicu_mrn', '=', SAMPLE_MRN)], limit=1)
        if patient:
            chart = self.search([('patient_id', '=', patient.id)], order='date desc', limit=1)
            if chart:
                return chart
        else:
            patient = Partner.create({
                'name': 'Baby Sample (Demo)',
                'is_nicu_patient': True,
                'nicu_mrn': SAMPLE_MRN,
                'nicu_birth_date': today - timedelta(days=26),
                'nicu_ga_weeks': 27,
                'nicu_ga_days': 4,
                'nicu_birth_weight': 900,
                'nicu_blood_group': 'AB+',
            })

        header = {
            'patient_id': patient.id,
            'diagnosis': 'Preterm, RDS',
            'consultant': 'Dr. Consultant',
            'head_circumference': 27.5,
            'parent_last_visit': today - timedelta(days=1),
            'ebm_given': 'no',
            'tfi_ml_kg_day': 152,
            'tpn_ml_hr': '4.3',
            'intralipids_ml_hr': '0.37',
            'nte_range': '34 - 35',
            'hr_alarm_low': '100', 'hr_alarm_high': '180',
            'rr_alarm_low': '30', 'rr_alarm_high': '60',
            'spo2_alarm_low': '88', 'spo2_alarm_high': '94',
            'mean_bp_alarm': '> GA (30)',
            'blood_gas_type': 'capillary',
            'gas_ph': '7.25 - 7.45', 'gas_pco2': '45 - 55',
            'gas_po2': '50 - 80', 'gas_hco3': '22 - 26',
            'other_instructions': 'Minimal handling.\nKeep baby warm.',
        }
        self.create(dict(header, date=today - timedelta(days=1), present_weight=980, previous_weight=960))

        chart = self.create(dict(
            header,
            date=today,
            present_weight=1000,
            previous_weight=980,
            investigations='CBC, CRP daily\nBlood gas every 12 hours\nAbdominal X-ray daily\nBlood culture',
            special_instructions='Follow up CBC & CRP.\nAbdominal X-ray once daily.\n'
                                 'Keep NPO, advance feeds as per consultant.\nFollow up blood culture.',
            **self._sample_assessment(today),
        ))

        # hourly grid
        lines = {line.code: line for line in chart.line_ids}
        Line = self.env['nicu.chart.line'].with_context(nicu_skip_recompute=True)
        for code, values in _sample_grid().items():
            Line.browse(lines[code].id).write({'h%s' % HOURS[h - 1]: v for h, v in values.items()})
        notes = {'iv1_site': 'TPN', 'iv2_site': 'LIPID', 'iv3_site': 'Nexium 0.2 mg/kg/day',
                 'bottling': 'NPO', 'glucose': 'Q6H', 'girth': 'Q12H', 'urine': 'Q3H',
                 'stool': 'Last: ' + fields.Date.to_string(today - timedelta(days=2))}
        for code, note in notes.items():
            Line.browse(lines[code].id).write({'note': note})
        chart._recompute_grid()

        # catheters
        cath = {
            'ett': {'size': '2.5', 'level': '7', 'insertion_date': today - timedelta(days=10)},
            'ngt': {'size': '6Fr', 'level': '13', 'insertion_date': today - timedelta(days=2)},
            'picc': {'size': '1Fr', 'level': 'R arm', 'insertion_date': today - timedelta(days=12)},
        }
        for line in chart.catheter_ids:
            if line.catheter_type in cath:
                line.write(cath[line.catheter_type])

        # shift check
        d = lambda n: (today + timedelta(days=n)).strftime('%d/%m/%y')
        extra = {
            'ID Bands On': ('✓', '✓'),
            'Central Line Dressing – Done': (d(-2), d(5)),
            'Ventilator Changed (Date)': (d(-3), d(4)),
            'Incubator Changed (Date)': (d(-7), d(7)),
            'Humidity Changed Daily': ('', '0800H'),
        }
        for line in chart.shift_check_ids:
            vals = {'day_check': '✓ RN-A', 'night_check': '✓ RN-B'}
            if line.name in extra:
                vals['value1'], vals['value2'] = extra[line.name]
            line.write(vals)

        # progress evaluation
        progress = [
            ('0700H', 'Baby received from night staff on mechanical ventilator, PC-PSV + VG mode, '
                      'PIP 18, PEEP 6, FiO2 25%. SpO2 maintaining 92-95%. TPN and lipid running via PICC line.', 'RN-A'),
            ('0800H', 'Morning care given. Weight checked 1000 g. Position changed. Mouth care done. '
                      'Skin intact, eye care done.', 'RN-A'),
            ('0900H', 'Doctor round done. Advised to continue same management. Abdominal X-ray done.', 'RN-A'),
            ('1000H', 'Blood sample sent to lab (CBC, CRP). RBS checked 5.8 mmol/L, doctor informed. '
                      'Medication given as per chart.', 'RN-A'),
            ('1200H', 'ETT suction given, small clear secretions. Baby comfortable, tolerating ventilator.', 'RN-A'),
            ('1400H', 'Parents visited, doctor explained the baby condition to the father. No other complaints.', 'RN-A'),
            ('1600H', 'Episode of desaturation SpO2 82%, self recovered with gentle stimulation. '
                      'Doctor informed, advised to observe.', 'RN-A'),
            ('1900H', 'Handed over to night staff. Vital signs stable. Lines patent.', 'RN-A'),
            ('2000H', 'Baby received on ventilator. Assessment done and documented. Vital signs checked and recorded.', 'RN-B'),
            ('2200H', 'Medication (Nexium) given as per chart. ETT suction given.', 'RN-B'),
            ('2400H', 'Care given, afebrile, BP stable. Urine output adequate. Baby resting comfortably.', 'RN-B'),
        ]
        chart.write({'note_ids': [(0, 0, {'date': today, 'time': t, 'note': n, 'signature': s})
                                  for t, n, s in progress]})
        return chart

    @api.model
    def _sample_assessment(self, today):
        common = {
            'bed_incubator': True, 'bed_servo': True, 'bed_servo_temp': '36.5', 'bed_humidity': '60',
            'skin_intact': True, 'skin_dry_warm': True, 'colour_pink': True,
            'eyes_clear': True, 'neuro_soft_flat': True, 'neuro_head_circ': '27.5',
            'tone_wnl': True, 'cap_brisk': True, 'cv_regular': True,
            'pulse_br_equal': True, 'pulse_fe_equal': True,
            'abd_soft': True, 'abd_flat': True, 'abd_bs_present': True,
            'skin_risk_score': '15',
            'resp_equal': True, 'resp_chest_equal': True, 'resp_unlabored': True,
            'resp_retr_mild': True, 'resp_last_cxr': today,
            'fall_risk_score': '17',
            'sign_date': today,
        }
        vals = {}
        for shift, extra in (
            ('day', {'sign_time': '0730H', 'nurse_name': 'Nurse A (Day)', 'signature': 'RN-A', 'job_no': '10562',
                     'comments': 'Baby stable on ventilator, NPO, TPN running.'}),
            ('night', {'sign_time': '1930H', 'nurse_name': 'Nurse B (Night)', 'signature': 'RN-B', 'job_no': '18340',
                       'comments': 'One episode of desaturation, self recovered.'}),
        ):
            for key, value in dict(common, **extra).items():
                vals['%s_%s' % (shift, key)] = value
        return vals

    @api.model
    def action_load_sample_data(self):
        chart = self._create_sample_data()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'nicu.chart',
            'res_id': chart.id,
            'view_mode': 'form',
            'target': 'current',
        }
