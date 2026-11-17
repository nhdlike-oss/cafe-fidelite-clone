from django.db import migrations


def premier_cafe(apps, schema_editor):
    # Etape 2 sur 3 : toutes les donnees de la v2 appartiennent au premier cafe (devoir 3, 2.1).
    # `.using(base)` : on travaille sur la base que la migration est en train de modifier
    # (et non sur la base « par defaut »), sinon `migrate --database=...` se tromperait de base.
    base = schema_editor.connection.alias
    Succursale = apps.get_model("fidelite", "Succursale")
    Transaction = apps.get_model("fidelite", "Transaction")
    User = apps.get_model("auth", "User")

    cafe, _ = Succursale.objects.using(base).get_or_create(nom="Café 1")
    Transaction.objects.using(base).filter(succursale__isnull=True).update(succursale=cafe)

    # Les employes de la v2 (baristas et gerants) travaillaient au seul cafe existant.
    employes = User.objects.using(base).filter(
        groups__name__in=["barista", "gerant"]).distinct()
    cafe.personnel.add(*employes)


class Migration(migrations.Migration):

    dependencies = [
        ("fidelite", "0005_v3_succursale"),
        ("auth", "0001_initial"),
    ]

    operations = [
        # Pas de retour arriere : detacher les transactions de leur cafe serait destructeur.
        migrations.RunPython(premier_cafe, migrations.RunPython.noop),
    ]
