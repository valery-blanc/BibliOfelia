"""FEAT-083 (coordonnées de l'usager) + FEAT-084 (cotisation par catégorie).

La recopie de l'ancien champ libre `address` vers les champs découpés se fait
**avant** sa suppression, et son inverse le reconstitue : sur une instance de
production, une migration qui ne sait pas revenir en arrière est une impasse.
"""
from decimal import Decimal

from django.db import migrations, models


def split_address(apps, schema_editor):
    """Première ligne de l'ancienne adresse → rue, le reste → complément."""
    Member = apps.get_model("members", "Member")
    for member in Member.objects.exclude(address="").only("id", "address"):
        lines = [line.strip() for line in (member.address or "").splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            continue
        member.address_street = lines[0][:200]
        member.address_extra = " ".join(lines[1:])[:200]
        member.save(update_fields=["address_street", "address_extra"])


def join_address(apps, schema_editor):
    Member = apps.get_model("members", "Member")
    for member in Member.objects.all():
        lines = [
            line
            for line in (
                member.address_street,
                member.address_extra,
                " ".join(
                    p for p in (member.address_postal_code, member.address_city) if p
                ),
                member.address_state,
                member.address_country,
            )
            if line
        ]
        if lines:
            member.address = "\n".join(lines)
            member.save(update_fields=["address"])


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0006_alter_member_address_alter_member_birth_date_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="member",
            name="email",
            field=models.EmailField(blank=True, max_length=254, verbose_name="email"),
        ),
        migrations.AddField(
            model_name="member",
            name="address_street",
            field=models.CharField(blank=True, max_length=200, verbose_name="rue et n°"),
        ),
        migrations.AddField(
            model_name="member",
            name="address_extra",
            field=models.CharField(
                blank=True, max_length=200, verbose_name="complément d'adresse"
            ),
        ),
        migrations.AddField(
            model_name="member",
            name="address_postal_code",
            field=models.CharField(blank=True, max_length=20, verbose_name="code postal"),
        ),
        migrations.AddField(
            model_name="member",
            name="address_city",
            field=models.CharField(blank=True, max_length=100, verbose_name="localité"),
        ),
        migrations.AddField(
            model_name="member",
            name="address_state",
            field=models.CharField(
                blank=True, max_length=100, verbose_name="état / province"
            ),
        ),
        migrations.AddField(
            model_name="member",
            name="address_country",
            field=models.CharField(blank=True, max_length=100, verbose_name="pays"),
        ),
        migrations.AddField(
            model_name="membercategory",
            name="membership_fee",
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal("0"),
                help_text="0 = pas de cotisation pour cette catégorie.",
                max_digits=10,
                verbose_name="cotisation annuelle",
            ),
        ),
        migrations.AlterField(
            model_name="member",
            name="notes",
            field=models.TextField(blank=True, verbose_name="commentaire"),
        ),
        migrations.RunPython(split_address, join_address),
        migrations.RemoveField(model_name="member", name="address"),
    ]
