from odoo import models


class RevivaIQAnalyticsService(models.AbstractModel):
    _name = "revivaiq.analytics.service"
    _description = "RevivaIQ Performance-Safe Analytics Service"

    DEFAULT_BATCH_LIMIT = 500
    MAX_BATCH_LIMIT = 2000

    def _get_safe_limit(self, limit=None):
        """
        Prevent unlimited analytics queries.

        RevivaIQ must never process millions of live records in one request.
        Large datasets should be processed with batching, read_group,
        SQL aggregation, or snapshot records.
        """
        if not limit:
            return self.DEFAULT_BATCH_LIMIT

        return min(int(limit), self.MAX_BATCH_LIMIT)

    def _get_company_domain(self, company=None):
        """
        Always keep analytics company-scoped.
        """
        target_company = company or self.env.company
        return [("company_id", "=", target_company.id)]

    def _combine_domains(self, *domains):
        """
        Small helper to safely combine multiple domain lists.
        """
        final_domain = []

        for domain in domains:
            if domain:
                final_domain.extend(domain)

        return final_domain

    def _search_limited(self, model_name, domain=None, limit=None, order="id desc"):
        """
        Safe search wrapper.

        Rules:
        - never use search([]) directly for analytics
        - always apply domain
        - always apply limit
        - always apply deterministic order
        """
        safe_limit = self._get_safe_limit(limit)
        safe_domain = domain or []

        return self.env[model_name].search(
            safe_domain,
            limit=safe_limit,
            order=order,
        )

    def _count_records(self, model_name, domain=None):
        """
        Safe count helper.
        search_count is cheaper than loading full records.
        """
        return self.env[model_name].search_count(domain or [])

    def _read_group_sum(self, model_name, domain, fields, groupby):
        """
        Foundation for future aggregate queries.

        Use read_group instead of loading all records when possible.
        """
        return self.env[model_name].read_group(
            domain or [],
            fields,
            groupby,
            lazy=False,
        )