from datetime import date

from django.db import migrations


def creer_donnees(apps, schema_editor):
    # Regle initiale = celle de la v1 (10 etampes), valable depuis toujours :
    # les soldes calcules apres la migration sont donc identiques a ceux de la v1.
    Regle = apps.get_model("fidelite", "RegleFidelite")
    Regle.objects.get_or_create(en_vigueur_le=date(2000, 1, 1),
                                defaults={"etampes_requises": 10})
    # Les deux roles (ADR-0007).
    Group = apps.get_model("auth", "Group")
    for nom in ("barista", "gerant"):
        Group.objects.get_or_create(name=nom)


class Migration(migrations.Migration):

    dependencies = [
        ("fidelite", "0003_v2_annulation_regle_audit"),
        ("auth", "0001_initial"),
    ]

    operations = [
        # Pas de retour arriere : supprimer la regle initiale ou les groupes serait destructeur.
        migrations.RunPython(creer_donnees, migrations.RunPython.noop),
    ]