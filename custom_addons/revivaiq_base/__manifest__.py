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
        "views/revivaiq_menu_views.xml",
        "views/dead_stock_views.xml",
        "views/customer_insight_views.xml",
        "views/analytics_snapshot_views.xml",
        "data/demo_data.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
    "auto_install": False,
}