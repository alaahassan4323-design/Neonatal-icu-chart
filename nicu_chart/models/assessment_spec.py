"""Physical assessment layout, exactly as printed on side 2 of the paper chart.

The same structure is used for the DAY and the NIGHT block. Fields are created
on nicu.chart with the prefixes ``day_`` and ``night_``; the form view and the
PDF report are generated from this spec so the three always stay identical.

Item types: bool (check box), char (small text), date, sub (sub-heading only)
"""

ASSESSMENT_COLUMNS = [
    [  # column 1
        ('1. BED TYPE', [
            ('bed_incubator', 'Incubator', 'bool'),
            ('bed_servo', 'Servo (°C Baby Mode)', 'bool'),
            ('bed_servo_temp', 'Servo °C', 'char'),
            ('bed_manual', 'Manual (°C Air Mode)', 'bool'),
            ('bed_manual_temp', 'Manual °C', 'char'),
            ('bed_humidity', 'Humidity %', 'char'),
            ('bed_radiant', 'Radiant Warmer', 'bool'),
            ('bed_skin_temp', 'Skin Temp. Mode', 'bool'),
            ('bed_cot', 'Cot', 'bool'),
        ]),
        ('2. SKIN', [
            ('skin_intact', 'Intact', 'bool'),
            ('skin_dry_warm', 'Dry/Warm', 'bool'),
            ('skin_diaphoretic', 'Diaphoretic', 'bool'),
            ('skin_cracked', 'Cracked/Peeling', 'bool'),
            ('skin_oedema', 'Oedema', 'bool'),
            ('skin_lesions', 'Lesions/Wounds*', 'bool'),
            ('skin_bruising', 'Bruising', 'bool'),
        ]),
        ('3. COLOUR', [
            ('colour_pink', 'Pink', 'bool'),
            ('colour_pale', 'Pale', 'bool'),
            ('colour_dusky', 'Dusky', 'bool'),
            ('colour_mottled', 'Mottled', 'bool'),
            ('colour_jaundice', 'Jaundice', 'bool'),
            ('colour_plethoric', 'Plethoric', 'bool'),
        ]),
    ],
    [  # column 2
        ('4. EYES', [
            ('eyes_clear', 'Clear', 'bool'),
            ('eyes_discharge', 'Discharge', 'bool'),
            ('eyes_puffy', 'Puffy', 'bool'),
        ]),
        ('5. NEUROLOGIC/FONTANELLES', [
            ('neuro_soft_flat', 'Soft / Flat', 'bool'),
            ('neuro_full_tense', 'Full / Tense', 'bool'),
            ('neuro_depressed', 'Depressed', 'bool'),
            ('neuro_bulging', 'Bulging', 'bool'),
            ('neuro_head_circ', 'Head Circumference (cm)', 'char'),
        ]),
        ('6. TONE', [
            ('tone_wnl', 'WNL for GA', 'bool'),
            ('tone_hypotonic', 'Hypotonic', 'bool'),
            ('tone_flaccid', 'Flaccid', 'bool'),
            ('tone_hypertonic', 'Hypertonic', 'bool'),
            ('tone_rigid', 'Rigid', 'bool'),
        ]),
        ('7. CAPILLARY REFILL', [
            ('cap_brisk', 'Brisk', 'bool'),
            ('cap_slow', 'Slow', 'bool'),
        ]),
    ],
    [  # column 3
        ('8. CARDIOVASCULAR', [
            ('_sub_heart', 'Heart sounds', 'sub'),
            ('cv_regular', 'Regular', 'bool'),
            ('cv_irregular', 'Irregular', 'bool'),
            ('cv_murmur', 'Murmur', 'bool'),
        ]),
        ('9. PULSES', [
            ('_sub_brachial', 'Brachial', 'sub'),
            ('pulse_br_equal', 'Equal', 'bool'),
            ('pulse_br_bounding', 'Bounding', 'bool'),
            ('pulse_br_weak', 'Weak', 'bool'),
            ('pulse_br_strong', 'Strong', 'bool'),
            ('_sub_femoral', 'Femoral', 'sub'),
            ('pulse_fe_equal', 'Equal', 'bool'),
            ('pulse_fe_bounding', 'Bounding', 'bool'),
            ('pulse_fe_weak', 'Weak', 'bool'),
            ('pulse_fe_strong', 'Strong', 'bool'),
        ]),
        ('10. ABDOMEN', [
            ('abd_soft', 'Soft', 'bool'),
            ('abd_firm', 'Firm', 'bool'),
            ('abd_flat', 'Flat', 'bool'),
            ('abd_distention', 'Distention', 'bool'),
            ('abd_loops', 'Bowel Loops Visible', 'bool'),
            ('abd_bs_present', 'Bowel Sounds Present', 'bool'),
            ('abd_bs_absent', 'Bowel Sounds Absent', 'bool'),
            ('abd_redness', 'Redness Discoloration', 'bool'),
        ]),
        ('11. SKIN RISK ASSESSMENT SCORE', [
            ('skin_risk_score', 'Score', 'char'),
        ]),
    ],
    [  # column 4
        ('12. RESPIRATORY', [
            ('_sub_breath', 'Breath sounds', 'sub'),
            ('resp_equal', 'Equal bilaterally', 'bool'),
            ('_sub_rl', 'R / L', 'sub'),
            ('resp_unequal_r', 'Unequal - R', 'bool'),
            ('resp_unequal_l', 'Unequal - L', 'bool'),
            ('resp_clear_r', 'Clear - R', 'bool'),
            ('resp_clear_l', 'Clear - L', 'bool'),
            ('resp_crackles_r', 'Crackles - R', 'bool'),
            ('resp_crackles_l', 'Crackles - L', 'bool'),
            ('resp_rales_r', 'Rales - R', 'bool'),
            ('resp_rales_l', 'Rales - L', 'bool'),
            ('resp_chest_equal', 'Equal chest movement', 'bool'),
            ('resp_labored', 'Labored', 'bool'),
            ('resp_unlabored', 'Unlaboured', 'bool'),
            ('resp_shallow', 'Shallow', 'bool'),
            ('resp_grunting', 'Grunting', 'bool'),
            ('resp_flaring', 'Nasal Flaring', 'bool'),
            ('_sub_retractions', 'Retractions', 'sub'),
            ('resp_retr_mild', 'Mild', 'bool'),
            ('resp_retr_moderate', 'Moderate', 'bool'),
            ('resp_retr_severe', 'Severe', 'bool'),
            ('resp_last_cxr', 'Last chest x-ray', 'date'),
        ]),
        ('13. FALL RISK ASSESSMENT', [
            ('fall_risk_score', 'Score', 'char'),
        ]),
    ],
]

# Footer of each block
ASSESSMENT_FOOTER = [
    ('comments', '*Comments', 'text'),
    ('sign_date', 'Date', 'date'),
    ('sign_time', 'Time', 'char'),
    ('nurse_name', 'Name', 'char'),
    ('signature', 'Signature', 'char'),
    ('job_no', 'Job No.', 'char'),
]

SHIFTS = [('day', 'DAY'), ('night', 'NIGHT')]


def iter_assessment_items():
    for column in ASSESSMENT_COLUMNS:
        for title, items in column:
            sub = ''
            for key, label, ftype in items:
                if ftype == 'sub':
                    sub = label
                    continue
                group = title.split('. ', 1)[-1].title()
                if sub in ('Brachial', 'Femoral'):
                    group = '%s %s' % (group, sub)
                yield key, '%s: %s' % (group, label), ftype
    for key, label, ftype in ASSESSMENT_FOOTER:
        yield key, label, ftype
