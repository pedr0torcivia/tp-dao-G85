"""Simplifica el ciclo del remito e incorpora incidencias de recepción.

* DESPACHADO y EN_TRANSITO se unifican: despachar deja el remito en tránsito.
  Los eventos «registrar salida» (DESPACHADO → EN_TRANSITO) se eliminan y los
  eventos de despacho pasan a EN_TRANSITO, por lo que la trazabilidad queda
  consistente con el nuevo ciclo.
* Se agrega RECIBIDO_CON_INCIDENCIAS y el resultado de recepción por ejemplar.
"""

from django.db import migrations, models


def unificar_despacho(apps, schema_editor):
    Remito = apps.get_model("logistica", "Remito")
    EventoRemito = apps.get_model("logistica", "EventoRemito")
    DetalleRemito = apps.get_model("logistica", "DetalleRemito")

    EventoRemito.objects.filter(estado_anterior="DESPACHADO", estado_nuevo="EN_TRANSITO").delete()
    EventoRemito.objects.filter(estado_nuevo="DESPACHADO").update(estado_nuevo="EN_TRANSITO")
    EventoRemito.objects.filter(estado_anterior="DESPACHADO").update(estado_anterior="EN_TRANSITO")
    Remito.objects.filter(estado="DESPACHADO").update(estado="EN_TRANSITO")

    DetalleRemito.objects.filter(condicion_recepcion="APTO").update(resultado_recepcion="CONFORME")
    DetalleRemito.objects.filter(condicion_recepcion="NO_APTO").update(resultado_recepcion="DANADO")


class Migration(migrations.Migration):
    dependencies = [("logistica", "0003_alter_remito_numero_and_more")]

    operations = [
        migrations.AddField(
            model_name="detalleremito",
            name="resultado_recepcion",
            field=models.CharField(
                blank=True,
                choices=[
                    ("CONFORME", "Llegó en condiciones"),
                    ("DANADO", "Llegó dañado"),
                    ("EXTRAVIADO", "Extraviado en el trayecto"),
                ],
                max_length=20,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name="remito",
            name="estado",
            field=models.CharField(
                choices=[
                    ("EN_PREPARACION", "En preparación"),
                    ("EMPAQUETADO", "Empaquetado"),
                    ("EN_TRANSITO", "En tránsito"),
                    ("RECIBIDO", "Recibido"),
                    ("RECIBIDO_CON_INCIDENCIAS", "Recibido con incidencias"),
                    ("CANCELADO", "Cancelado"),
                ],
                default="EN_PREPARACION",
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name="eventoremito",
            name="estado_anterior",
            field=models.CharField(blank=True, max_length=30, null=True),
        ),
        migrations.AlterField(
            model_name="eventoremito",
            name="estado_nuevo",
            field=models.CharField(
                choices=[
                    ("EN_PREPARACION", "En preparación"),
                    ("EMPAQUETADO", "Empaquetado"),
                    ("EN_TRANSITO", "En tránsito"),
                    ("RECIBIDO", "Recibido"),
                    ("RECIBIDO_CON_INCIDENCIAS", "Recibido con incidencias"),
                    ("CANCELADO", "Cancelado"),
                ],
                max_length=30,
            ),
        ),
        migrations.RunPython(unificar_despacho, migrations.RunPython.noop),
    ]
