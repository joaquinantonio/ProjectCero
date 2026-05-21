from django.contrib.admin.apps import AdminConfig


class CeroAdminConfig(AdminConfig):
    default_site = "config.admin_site.CeroAdminSite"