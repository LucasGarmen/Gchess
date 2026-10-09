from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import CosmeticLoadout
from .i18n import current_language
from .shop_texts import TEXTS

from .cosmetic_catalog import DEFAULTS, FREE_ITEMS, AVAILABLE_ITEMS, AVATAR_ACCESSORY_SLOTS, usable_loadout

def context(request):
    cached=getattr(request,'_shop_context',None)
    if cached is not None:return cached
    loadout=CosmeticLoadout.objects.filter(user=request.user).first() if request.user.is_authenticated else None
    selected=usable_loadout(loadout or DEFAULTS)
    texts=TEXTS[current_language(request)]
    selected_names={kind:texts['items'][kind][selected[kind] if isinstance(selected,dict) else getattr(selected,kind)] for kind in FREE_ITEMS}
    request._shop_context=dict(shop_texts=texts,cosmetics=selected,cosmetic_names=selected_names)
    return request._shop_context

def shop(request):
    choices=context(request)
    selected=choices['cosmetics']
    groups=[]
    all_cards=[]
    for kind,items in FREE_ITEMS.items():
        current=selected[kind] if isinstance(selected,dict) else getattr(selected,kind)
        cards=[dict(kind=kind,item=item,label=(choices['shop_texts']['avatar_label']+' '+choices['shop_texts']['items'][kind][item]) if kind=='avatar' and choices['shop_texts']['items'][kind][item].isdigit() else choices['shop_texts']['items'][kind][item],selected=current==item,locked=item not in AVAILABLE_ITEMS[kind]) for item in items]
        all_cards.extend(cards)
        if kind in ('face','eyewear','earrings'):
            if kind=='face':groups.append(dict(kind='face',label=choices['shop_texts']['categories']['face'],cards=[],sections=[]))
            groups[-1]['cards'].extend(cards)
            groups[-1]['sections'].append(dict(label=choices['shop_texts']['subtitles'][kind],cards=cards))
        else:groups.append(dict(kind=kind,label=choices['shop_texts']['categories'][kind],cards=cards))
    return render(request,'games/shop.html',dict(**choices,shop_groups=groups,shop_cards=all_cards,just_saved=request.GET.get('saved')=='1'))

@login_required
@require_POST
def equip(request):
    kind=request.POST.get('kind');item=request.POST.get('item')
    if kind not in FREE_ITEMS or item not in FREE_ITEMS[kind]:return HttpResponseBadRequest('Invalid cosmetic.')
    if item not in AVAILABLE_ITEMS[kind]:return HttpResponseForbidden('Cosmetic unavailable.')
    with transaction.atomic():
        # get_or_create handles the unique-account race; field-only saves avoid lost combinations.
        loadout,_=CosmeticLoadout.objects.get_or_create(user=request.user)
        loadout=CosmeticLoadout.objects.select_for_update().get(pk=loadout.pk)
        avatar_changed=kind=='avatar' and loadout.avatar!=item
        values=usable_loadout(loadout)
        values[kind]=item
        if avatar_changed:
            for slot in AVATAR_ACCESSORY_SLOTS:values[slot]=DEFAULTS[slot]
        for slot,value in values.items():setattr(loadout,slot,value)
        loadout.save(update_fields=list(values))
    return redirect(reverse('shop')+'?saved=1#shop-'+('face' if kind in ('eyewear','earrings') else kind))
