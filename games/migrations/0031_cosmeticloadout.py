from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    dependencies=[('games','0030_gameinvitation_search_seen_at'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='CosmeticLoadout',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('avatar',models.CharField(choices=[('explorer','Explorer'),('strategist','Strategist')],default='explorer',max_length=20)),('board',models.CharField(choices=[('rustic','Rustic')],default='rustic',max_length=20)),('accessory',models.CharField(choices=[('none','None'),('cap','Cap')],default='none',max_length=20)),('user',models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,related_name='cosmetic_loadout',to=settings.AUTH_USER_MODEL))])]
