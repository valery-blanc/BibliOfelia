"""FEAT-072 — `MemberChild` devient `MemberFamilyMember`.

Renommage plutôt que suppression/recréation : les fiches déjà saisies au
Sprint 28 doivent survivre. L'`age` (entier) devient une **année de naissance**,
convertie ici — un âge saisi une fois devient faux l'année suivante.
"""
from datetime import date

from django.db import migrations, models


def age_to_birth_year(apps, schema_editor):
    """`birth_year` contient encore les âges hérités : on les convertit."""
    Family = apps.get_model("members", "MemberFamilyMember")
    current_year = date.today().year
    for pk, value in Family.objects.values_list("pk", "birth_year"):
        if value and value < 200:  # un âge, pas une année
            Family.objects.filter(pk=pk).update(birth_year=current_year - value)


def birth_year_to_age(apps, schema_editor):
    Family = apps.get_model("members", "MemberFamilyMember")
    current_year = date.today().year
    for pk, value in Family.objects.values_list("pk", "birth_year"):
        if value and value >= 200:
            Family.objects.filter(pk=pk).update(birth_year=current_year - value)


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0004_remove_member_parent_account_member_spoken_languages_and_more"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="MemberChild",
            new_name="MemberFamilyMember",
        ),
        migrations.AlterModelOptions(
            name="memberfamilymember",
            options={
                "ordering": ["first_name"],
                "verbose_name": "membre de la famille",
                "verbose_name_plural": "membres de la famille",
            },
        ),
        migrations.AlterField(
            model_name="memberfamilymember",
            name="member",
            field=models.ForeignKey(
                on_delete=models.deletion.CASCADE,
                related_name="family",
                to="members.member",
            ),
        ),
        migrations.RenameField(
            model_name="memberfamilymember",
            old_name="age",
            new_name="birth_year",
        ),
        migrations.AlterField(
            model_name="memberfamilymember",
            name="birth_year",
            field=models.PositiveSmallIntegerField(
                blank=True, null=True, verbose_name="année de naissance"
            ),
        ),
        migrations.AddField(
            model_name="memberfamilymember",
            name="is_adult",
            field=models.BooleanField(default=False, verbose_name="adulte"),
        ),
        migrations.RunPython(age_to_birth_year, birth_year_to_age),
    ]
