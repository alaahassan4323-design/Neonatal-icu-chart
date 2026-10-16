{
    'name': 'Neonatal ICU Chart',
    'version': '19.0.1.0.0',
    'summary': 'Neonatal ICU 24-hour chart: flowsheet, IV & fluid balance, physical assessment, progress evaluation',
    'description': """
Neonatal ICU Chart
==================
Digital version of the paper "Neonatal ICU Chart - Patient I.D." form, kept
identical in structure:

* Side 1: Nursing care, vital signs (with graph), ventilation, IV / medications /
  blood products, feeding, total intake, outputs and 24-hour fluid balance,
  hour by hour (01 - 24).
* Side 2: Physical assessment (shift check, day & night), progress evaluation.
* Printable PDF that follows the paper layout (A3 landscape).
""",
    'category': 'Healthcare',
    'author': 'Custom',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'contacts'],
    'data': [
        'security/nicu_security.xml',
        'security/ir.model.access.csv',
        'data/nicu_actions.xml',
        'report/nicu_chart_report.xml',
        'views/res_partner_views.xml',
        'views/nicu_chart_views.xml',
        'views/menus.xml',
    ],
    'demo': [
        'demo/nicu_demo.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'nicu_chart/static/src/scss/nicu_chart.scss',
        ],
    },
    'application': True,
    'installable': True,
}
