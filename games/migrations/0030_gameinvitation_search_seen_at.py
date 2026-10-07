from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('games', '0029_chessgame_blindfold_only_and_more')]
    operations = [migrations.AddField(model_name='gameinvitation', name='search_seen_at', field=models.DateTimeField(blank=True, null=True))]
