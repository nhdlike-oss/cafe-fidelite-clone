import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    # Etape 3 sur 3 : maintenant que chaque transaction a un cafe, la colonne devient obligatoire.

    dependencies = [("fidelite", "0006_donnees_initiales_v3")]

    operations = [
        migrations.AlterField(
            model_name="transaction",
            name="succursale",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="transactions", to="fidelite.succursale"),
        ),
    ]
