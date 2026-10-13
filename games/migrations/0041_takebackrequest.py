from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies = [('games','0040_gameexperienceevent')]
    operations = [migrations.CreateModel(name='TakebackRequest',fields=[
        ('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),
        ('move_id',models.PositiveBigIntegerField()),
        ('requested_color',models.CharField(max_length=10)),
        ('status',models.CharField(default='pending',max_length=10)),
        ('game',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name='takeback_request',to='games.chessgame')),
    ])]
