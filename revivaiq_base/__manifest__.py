{
    "name": "RevivaIQ - Sales Recovery & Core Insights",
    "summary": "Sales recovery and inventory intelligence foundation for Odoo.",
    "description": """
RevivaIQ Base provides the foundation for sales recovery, inactive customer insights,
dead stock intelligence, executive dashboard, and export-ready operational analytics.
    """,
    "version": "18.0.1.0.0",
    "category": "Sales",
    "author": "CodeNRS",
    "website": "https://codenrs.com/revivaiq",
    "support": "support@codenrs.com",
    "license": "OPL-1",
    "depends": [
        "base",
        "sale_management",
        "stock"
    ],
    "data": [
        "security/revivaiq_security.xml",
        "security/ir.model.access.csv",

        "data/dashboard_data.xml",
        "data/server_actions.xml",

        "views/analysis_wizard_views.xml",
        "views/dead_stock_views.xml",
        "views/customer_insight_views.xml",
        "views/analytics_snapshot_views.xml",
        "views/revivaiq_menu_views.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'revivaiq_base/static/css/dashboard_style.css',  
        ],
    },
    "images": [
    "static/description/thumbnail.png",
    "static/description/banner.png",
    "static/description/screenshot_01_dashboard_overview.png",
    "static/description/screenshot_02_dead_stock_list.png",
    "static/description/screenshot_03_dead_stock_form.png",
    "static/description/screenshot_04_customer_insights_list.png",
    "static/description/screenshot_05_customer_insights_form.png",
    "static/description/screenshot_06_analytics_snapshot_list.png",
    "static/description/screenshot_07_analytics_snapshot_form.png",
    "static/description/screenshot_08_dead_stock_analysis_wizard.png",
    "static/description/screenshot_09_customer_search_filters.png",
    ],
    "price": 149.00,
    "currency": "USD",
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}