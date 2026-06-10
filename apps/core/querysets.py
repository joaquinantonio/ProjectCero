from django.db import models


class ActiveQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class FeaturedQuerySet(ActiveQuerySet):
    def featured(self):
        return self.active().filter(is_featured=True)



