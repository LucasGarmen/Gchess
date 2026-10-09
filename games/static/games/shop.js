(function () {
    var saving = false;
    function openSelectedCategory() {
        var id = window.location.hash.slice(1);
        if (!/^shop-(avatar|board|pieces|accessory|clothing|hairstyle|face)$/.test(id)) return;
        var category = document.getElementById(id);
        if (category) category.open = true;
    }
    openSelectedCategory();
    window.addEventListener('hashchange', openSelectedCategory);
    // Native POST remains the fallback. Enhanced saves refresh server-rendered previews
    // without navigating away from the catalog or losing the open categories.
    document.addEventListener('submit', async function (event) {
        var form = event.target;
        if (!form.matches('.shop-card form') || !window.fetch || !window.DOMParser) return;
        event.preventDefault();
        if (saving) return;
        var page = document.querySelector('.shop-page');
        var feedback = page.querySelector('.shop-feedback');
        var scrollY = window.scrollY;
        var open = Array.from(page.querySelectorAll('.shop-category[open]')).map(function (el) {return el.id;});
        var categoryId = form.closest('.shop-category').id;
        saving = true;
        page.setAttribute('aria-busy','true');
        feedback.textContent = page.dataset.saving;
        try {
            var response = await window.fetch(form.action, {method:'POST',body:new FormData(form),credentials:'same-origin'});
            if (!response.ok) throw new Error('Save failed');
            var parsed = new DOMParser().parseFromString(await response.text(),'text/html');
            var refreshed = parsed.querySelector('.shop-page');
            if (!refreshed) {
                // An expired session follows the same login flow as the native form.
                if (response.redirected && new URL(response.url).origin === window.location.origin) {window.location.assign(response.url);return;}
                throw new Error('Missing shop response');
            }
            page.innerHTML = refreshed.innerHTML;
            var currentNav=document.querySelector('.nav-avatar');
            var refreshedNav=parsed.querySelector('.nav-avatar');
            if(currentNav && refreshedNav)currentNav.innerHTML=refreshedNav.innerHTML;
            open.forEach(function (id) {var el=document.getElementById(id);if(el)el.open=true;});
            // Keep keyboard users in the same category after replacing its item buttons.
            var category=document.getElementById(categoryId);
            if(category)category.querySelector('summary').focus({preventScroll:true});
            window.scrollTo(0,scrollY);
        } catch (error) {
            page.querySelector('.shop-feedback').textContent=page.dataset.saveError;
        } finally {
            saving=false;
            page.removeAttribute('aria-busy');
        }
    });
})();
