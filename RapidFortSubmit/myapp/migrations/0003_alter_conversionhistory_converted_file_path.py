# Generated by Django 5.1.3 on 2024-11-22 17:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("myapp", "0002_conversionhistory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="conversionhistory",
            name="converted_file_path",
            field=models.TextField(),
        ),
    ]