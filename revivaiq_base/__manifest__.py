{
    "name": "RevivaIQ - Sales Recovery & Core Insights",
    "summary": "Dead stock management, slow moving inventory analytics, inactive customer recovery, and executive sales intelligence dashboard for Odoo.",
    "description": """
RevivaIQ Base is an Odoo operational intelligence module for dead stock management,
slow moving inventory tracking, inactive customer recovery, sales recovery analytics,
and revenue risk monitoring.

It helps sales, inventory, and business managers identify hidden revenue loss from
non-moving stock and inactive customers through an Odoo-native executive dashboard,
analysis wizards, advanced search filters, and analytics snapshot history.

Key Features:
- Dead stock detection and inventory risk scoring
- Slow moving inventory and stock recovery insights
- Inactive customer tracking and customer recovery opportunities
- Sales recovery dashboard for business owners and managers
- Revenue risk analytics and snapshot history
- Advanced search, filters, grouping, and operational workflows
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
        "stock",
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
    "assets": {
        "web.assets_backend": [
            "revivaiq_base/static/css/dashboard_style.css",
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