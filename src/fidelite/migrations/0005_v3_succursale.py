import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    # Etape 1 sur 3 : on AJOUTE la table Succursale et une colonne encore facultative.
    # (PostgreSQL refuse de modifier une colonne dans la meme transaction qu'une mise
    # a jour de ses donnees : on separe donc en trois migrations.)

    dependencies = [
        ("fidelite", "0004_donnees_initiales_v2"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Succursale",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True,
                                           serialize=False, verbose_name="ID")),
                ("nom", models.CharField(max_length=100, unique=True)),
                ("active", models.BooleanField(default=True)),
                ("personnel", models.ManyToManyField(
                    blank=True, related_name="succursales", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["nom"]},
        ),
        migrations.AddField(
            model_name="transaction",
            name="succursale",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions", to="fidelite.succursale"),
        ),
    ]
