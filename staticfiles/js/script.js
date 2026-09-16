console.log("FragVerse Loaded Successfully");

// ===== PREMIUM NAVBAR & SEARCH FUNCTIONALITY =====

document.addEventListener('DOMContentLoaded', function() {

    const searchInputModal = document.getElementById('searchInputModal');
    const searchSubmitBtn = document.getElementById('searchSubmitBtn');
    const searchSuggestionsDiv = document.getElementById('searchSuggestions');
    const suggestionsList = document.querySelector('.suggestions-list');
    const searchEmptyState = document.getElementById('searchEmptyState');
    const searchModal = document.getElementById('searchModal');

    let debounceTimer;
    function debounceSearch(callback, delay = 300) {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(callback, delay);
    }

    async function fetchSearchSuggestions(query) {
        if (query.length < 1) {
            if (searchSuggestionsDiv) searchSuggestionsDiv.style.display = 'none';
            if (searchEmptyState) {
                searchEmptyState.style.display = 'block';
                searchEmptyState.textContent = 'Start typing to see suggestions...';
            }
            return;
        }

        try {
            const response = await fetch(`/api/search-suggestions/?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            if (data.results && data.results.length > 0) {
                displaySuggestions(data.results);
                if (searchSuggestionsDiv) searchSuggestionsDiv.style.display = 'block';
                if (searchEmptyState) searchEmptyState.style.display = 'none';
            } else {
                if (searchSuggestionsDiv) searchSuggestionsDiv.style.display = 'none';
                if (searchEmptyState) {
                    searchEmptyState.style.display = 'block';
                    searchEmptyState.textContent = 'No products found';
                }
            }
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            if (searchEmptyState) {
                searchEmptyState.style.display = 'block';
                searchEmptyState.textContent = 'No products found';
            }
            if (searchSuggestionsDiv) searchSuggestionsDiv.style.display = 'none';
        }
    }

    function displaySuggestions(results) {
        if (!suggestionsList) return;
        suggestionsList.innerHTML = '';

        results.forEach(product => {
            const suggestionItem = document.createElement('a');
            suggestionItem.href = product.url;
            suggestionItem.className = 'suggestion-item text-decoration-none d-flex gap-2';

            const imageHtml = product.image
                ? `<img src="${product.image}" alt="${product.name}" class="suggestion-image">`
                : `<div class="suggestion-image" style="background: rgba(200, 169, 81, 0.1); display: flex; align-items: center; justify-content: center;"><i class="fas fa-image" style="color: rgba(200, 169, 81, 0.5);"></i></div>`;

            suggestionItem.innerHTML = `
                ${imageHtml}
                <div class="suggestion-content flex-grow-1">
                    <div class="suggestion-name">${product.name}</div>
                    <div class="suggestion-brand">${product.brand}</div>
                </div>
                <div class="suggestion-price">₹${parseFloat(product.price).toFixed(2)}</div>
            `;

            suggestionsList.appendChild(suggestionItem);
        });
    }

    if (searchInputModal) {
        searchInputModal.addEventListener('input', function(e) {
            const query = e.target.value.trim();
            debounceSearch(() => {
                fetchSearchSuggestions(query);
            });
        });

        searchInputModal.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                const query = searchInputModal.value.trim();
                if (query) {
                    window.location.href = `/search/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    if (searchSubmitBtn) {
        searchSubmitBtn.addEventListener('click', function() {
            const query = searchInputModal.value.trim();
            if (query) {
                window.location.href = `/search/?q=${encodeURIComponent(query)}`;
            }
        });
    }

    if (searchModal) {
        searchModal.addEventListener('hidden.bs.modal', function() {
            if (searchInputModal) searchInputModal.value = '';
            if (searchSuggestionsDiv) searchSuggestionsDiv.style.display = 'none';
            if (searchEmptyState) {
                searchEmptyState.style.display = 'block';
                searchEmptyState.textContent = 'Start typing to see suggestions...';
            }
        });

        searchModal.addEventListener('shown.bs.modal', function() {
            if (searchInputModal) searchInputModal.focus();
        });
    }

    document.addEventListener('click', function(e) {
        const profileDropdown = document.querySelector('.profile-dropdown');
        const profileLink = profileDropdown ? profileDropdown.querySelector('[data-bs-toggle="dropdown"]') : null;

        if (profileDropdown && !profileDropdown.contains(e.target)) {
            const dropdown = bootstrap.Dropout ? bootstrap.Dropdown.getInstance(profileLink) : null;
            if (dropdown) {
                dropdown.hide();
            }
        }
    });

    function showToast(message) {
        const existing = document.querySelector('.frag-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'frag-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'toastOut 0.25s ease forwards';
        }, 2200);

        setTimeout(() => {
            toast.remove();
        }, 2600);
    }

    function updateCartBadge(count) {
        const badge = document.querySelector('.cart-badge');
        const cartLink = document.querySelector('.cart-icon-link');

        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline-flex' : 'none';
        } else if (count > 0 && cartLink) {
            const newBadge = document.createElement('span');
            newBadge.className = 'cart-badge';
            newBadge.textContent = count;
            cartLink.appendChild(newBadge);
        }
    }

    const orderDetailsModalElement = document.getElementById('orderDetailsModal');
    const orderDetailsModal = orderDetailsModalElement
        ? bootstrap.Modal.getOrCreateInstance(orderDetailsModalElement)
        : null;
    const orderDetailsBody = document.getElementById('orderDetailsModalBody');

    document.querySelectorAll('.js-order-details').forEach(button => {
        button.addEventListener('click', event => {
            event.preventDefault();
            const source = document.getElementById(button.dataset.orderSource);

            if (!source || !orderDetailsBody) {
                window.location.href = button.href;
                return;
            }

            orderDetailsBody.innerHTML = source.innerHTML;
            orderDetailsModal?.show();
        });
    });

    document.querySelectorAll('[data-cart-quantity-action]').forEach(button => {
        button.addEventListener('click', async event => {
            event.preventDefault();

            const row = button.closest('[data-cart-item]');
            if (!row || button.dataset.loading === 'true') return;

            button.dataset.loading = 'true';
            button.classList.add('is-loading');

            try {
                const response = await fetch(button.href, {
                    headers: { 'X-Requested-With': 'XMLHttpRequest' }
                });
                const data = await response.json();

                if (!response.ok || !data.success) {
                    showToast(data.message || 'Unable to update cart.');
                    return;
                }

                if (data.removed) {
                    row.remove();
                } else {
                    row.querySelector('.cart-item-quantity').textContent = data.quantity;
                    row.querySelector('.cart-item-subtotal').textContent = `₹${data.subtotal}`;
                }

                document.querySelectorAll('.cart-summary-subtotal, .cart-summary-total')
                    .forEach(element => {
                        element.textContent = `₹${data.cart_total}`;
                    });
                updateCartBadge(data.cart_count);

                if (data.cart_count === 0) {
                    const cartLayout = row.closest('.cart-layout');
                    const itemsPanel = cartLayout?.querySelector('.cart-items-panel');
                    const summaryPanel = cartLayout?.querySelector('.cart-summary-panel');

                    if (itemsPanel) {
                        itemsPanel.innerHTML = `
                            <div class="cart-empty-state">
                                <div class="empty-cart-icon"><i class="fa-solid fa-bag-shopping"></i></div>
                                <h2>Your cart is empty</h2>
                                <p>Looks like you haven't added any fragrances yet.</p>
                                <a href="/shop/" class="btn btn-continue-shopping large-btn">
                                    <i class="fa-solid fa-arrow-left"></i> Continue Shopping
                                </a>
                            </div>
                        `;
                    }
                    if (summaryPanel) summaryPanel.remove();
                }
            } catch (error) {
                console.error('Cart quantity error:', error);
                showToast('Something went wrong. Please try again.');
            } finally {
                button.dataset.loading = 'false';
                button.classList.remove('is-loading');
            }
        });
    });

    const variantModalElement = document.getElementById('cartVariantModal');
    const variantModal = variantModalElement
        ? bootstrap.Modal.getOrCreateInstance(variantModalElement)
        : null;
    const variantList = document.getElementById('cartVariantOptionsList');
    const variantProduct = document.getElementById('cartVariantProduct');
    const variantEmpty = document.getElementById('cartVariantEmpty');
    const variantConfirm = document.getElementById('cartVariantConfirm');
    let pendingCartForm = null;

    function productNameForForm(form) {
        const card = form.closest('.shop-product-card, article');
        const name = card?.querySelector(
            '.shop-product-name-link h3, .shop-product-name, h3'
        );
        return name?.textContent.trim() || 'This product';
    }

    function openVariantModal(form) {
        const options = [...form.querySelectorAll(
            '.cart-variant-options option'
        )];

        pendingCartForm = form;
        variantProduct.textContent = productNameForForm(form);
        variantList.innerHTML = '';
        variantEmpty.hidden = options.length > 0;
        variantConfirm.disabled = options.length === 0;

        options.forEach((option, index) => {
            const choice = document.createElement('label');
            choice.className = 'cart-variant-choice';
            choice.innerHTML = `
                <input type="radio" name="cart-variant-choice" value="${option.value}" ${index === 0 ? 'checked' : ''}>
                <span class="cart-variant-choice-copy">
                    <strong>${option.textContent.trim() || 'Standard option'}</strong>
                    <small>Available for immediate dispatch</small>
                </span>
                <span class="cart-variant-choice-price">₹${option.dataset.price}</span>
            `;
            variantList.appendChild(choice);
        });

        variantModal?.show();
    }

    async function submitCartForm(form) {
        const button = form.querySelector('.shop-add-cart-btn');
        const originalHTML = button?.innerHTML || '';

        if (button) button.disabled = true;

        try {
            const response = await fetch(form.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': form.querySelector(
                        'input[name="csrfmiddlewaretoken"]'
                    )?.value,
                },
                body: new FormData(form)
            });

            if (response.redirected) {
                window.location.href = response.url;
                return;
            }

            const data = await response.json();
            if (data.login_required) {
                window.location.href = `/login/?next=${encodeURIComponent(window.location.href)}`;
                return;
            }

            showToast(data.message || (data.success
                ? 'Product added to cart successfully.'
                : 'Unable to add product to cart.'));

            if (data.success) updateCartBadge(data.cart_count || 0);
        } catch (error) {
            console.error('AJAX cart error:', error);
            showToast('Something went wrong. Please try again.');
        } finally {
            if (button) {
                button.disabled = false;
                button.innerHTML = originalHTML;
            }
        }
    }

    document.querySelectorAll('.js-add-to-cart-form').forEach(form => {
        form.addEventListener('submit', event => {
            event.preventDefault();

            if (document.body.dataset.userAuthenticated !== 'true') {
                window.location.href = `/login/?next=${encodeURIComponent(window.location.href)}`;
                return;
            }

            if (form.classList.contains('product-detail-cart-form')) {
                submitCartForm(form);
                return;
            }

            openVariantModal(form);
        });
    });

    variantConfirm?.addEventListener('click', () => {
        const selected = variantList.querySelector(
            'input[name="cart-variant-choice"]:checked'
        );
        const variantSelect = pendingCartForm?.querySelector('.cart-variant-options');

        if (!selected || !variantSelect || !pendingCartForm) return;

        variantSelect.value = selected.value;
        variantModal?.hide();
        submitCartForm(pendingCartForm);
    });

   

// WISHLIST TOGGLE


const wishlistButtons = document.querySelectorAll(
    '.js-wishlist-btn'
);

wishlistButtons.forEach(button => {

    button.addEventListener(
        'click',
        async function(event) {

            event.preventDefault();

            // Prevent double clicking while request is processing
            if (button.dataset.loading === 'true') {
                return;
            }

            button.dataset.loading = 'true';

            const icon = button.querySelector('i');

            try {

                const response = await fetch(
                    button.href,
                    {
                        method: 'GET',

                        headers: {
                            'X-Requested-With':
                                'XMLHttpRequest'
                        }
                    }
                );

                const data = await response.json();


            
                // LOGIN REQUIRED
                

                if (data.login_required) {

                    window.location.href =
                        `/login/?next=${encodeURIComponent(
                            window.location.href
                        )}`;

                    return;
                }


                
                // SUCCESS
               

                if (data.success) {

                    
                    // PRODUCT ADDED

                    if (data.is_wishlisted) {

                        button.classList.add(
                            'is-active'
                        );

                        button.setAttribute(
                            'title',
                            'Remove from Wishlist'
                        );

                        if (icon) {

                            icon.classList.remove(
                                'fa-regular'
                            );

                            icon.classList.add(
                                'fa-solid'
                            );
                        }

                    }

                    
                    // PRODUCT REMOVED
                    

                    else {

                        button.classList.remove(
                            'is-active'
                        );

                        button.setAttribute(
                            'title',
                            'Add to Wishlist'
                        );

                        if (icon) {

                            icon.classList.remove(
                                'fa-solid'
                            );

                            icon.classList.add(
                                'fa-regular'
                            );
                        }
                    }


                    
                    // SHOW MESSAGE

                    showToast(
                        data.message ||
                        'Wishlist updated.'
                    );

                }

                else {

                    showToast(
                        data.message ||
                        'Unable to update wishlist.'
                    );
                }


            } catch (error) {

                console.error(
                    'Wishlist AJAX error:',
                    error
                );

                showToast(
                    'Unable to update wishlist.'
                );

            } finally {

                button.dataset.loading = 'false';
            }

        }
    );

});



    const filterToggle = document.getElementById('shopFilterToggle');
    const drawer = document.getElementById('shopFilterDrawer');
    const backdrop = document.getElementById('shopDrawerBackdrop');
    const drawerClose = document.getElementById('shopFilterClose');

    if (filterToggle && drawer && backdrop) {
        filterToggle.addEventListener('click', function() {
            drawer.classList.add('is-open');
            backdrop.classList.add('is-visible');
            drawer.setAttribute('aria-hidden', 'false');
        });

        function closeDrawer() {
            drawer.classList.remove('is-open');
            backdrop.classList.remove('is-visible');
            drawer.setAttribute('aria-hidden', 'true');
        }

        drawerClose?.addEventListener('click', closeDrawer);
        backdrop.addEventListener('click', closeDrawer);
    }

});

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#' && document.querySelector(href)) {
            e.preventDefault();
            const target = document.querySelector(href);
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});




const couponCopyButtons =
    document.querySelectorAll('.coupon-copy-btn');

couponCopyButtons.forEach(button => {

    button.addEventListener('click', async function() {

        const code =
            button.dataset.code;

        try {

            await navigator.clipboard.writeText(code);

            showToast(
                `Coupon ${code} copied successfully.`
            );

            const originalText =
                button.textContent;

            button.textContent = 'Copied!';

            setTimeout(() => {

                button.textContent =
                    originalText;

            }, 1500);

        } catch (error) {

            showToast(
                `Copy this coupon: ${code}`
            );

        }

    });

});