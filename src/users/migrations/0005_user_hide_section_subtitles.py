from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_user_user_org_role_idx_user_user_org_active_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='hide_section_subtitles',
            field=models.BooleanField(
                default=False,
                verbose_name='Приховати підписи під заголовками',
            ),
        ),
    ]
