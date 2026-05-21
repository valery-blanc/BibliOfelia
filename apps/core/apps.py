from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        self._register_auditlog()

    @staticmethod
    def _register_auditlog() -> None:
        """SPEC §9.6 : audit log sur Member, BibliographicRecord, Item, Loan, Setting, User."""
        from auditlog.registry import auditlog

        from apps.accounts.models import User
        from apps.catalog.models import BibliographicRecord, Item
        from apps.core.models import Setting
        from apps.loans.models import Loan
        from apps.members.models import Member

        for model in (Setting, BibliographicRecord, Item, Member, Loan, User):
            if not auditlog.contains(model):
                auditlog.register(model)
