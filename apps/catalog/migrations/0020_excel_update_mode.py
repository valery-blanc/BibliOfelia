# FEAT-079 — mode « mise à jour des exemplaires » du catalogage Excel.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0019_alter_category_parent_alter_location_parent'),
    ]

    operations = [
        migrations.AlterField(
            model_name='excelcatalogjob',
            name='mode',
            field=models.CharField(
                choices=[
                    ('verify', 'Vérification'),
                    ('import', 'Import'),
                    ('update', 'Mise à jour'),
                ],
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='excelcatalogjob',
            name='updated',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='excelcatalogjob',
            name='unchanged',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
