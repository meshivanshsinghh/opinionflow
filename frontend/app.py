import streamlit as st
import requests

API_URL = 'http://127.0.0.1:8000/api/v1/products/discover'

st.set_page_config(page_title="OpinionFlow", layout="wide")

with st.sidebar: 
    st.title("History")
    st.info("History coming soon!")
    

st.title("OpinionFlow")

col1, col2 = st.columns([6, 1])
with col1:
    query = st.text_input("Search for a product", "", key="query")
    
with col2:
    if "max_entries" not in st.session_state:
        st.session_state["max_entries"] = 5
        
# max entries popup
# Todo: Not clear after selecting
if st.session_state.get("show_max_popup", False):
    with st.popover("Set max entries per source"):
        max_entries = st.number_input("Max entries per source", min_value=1, 
                                      max_value = 10, value=st.session_state["max_entries"], step=1)
        if st.button("Apply", key="apply_max_entries"):
            st.session_state["max_entries"] = max_entries
            st.session_state["show_max_popup"] = False
            
# custom product popup
if "show_custom_popup" not in st.session_state:
    st.session_state["show_custom_popup"] = False
if st.session_state["show_custom_popup"]:
    with st.popover("Add your own product link"):
        custom_url = st.text_input("Paste product URL", key="custom_url")
        if st.button("Add Product", key="add_custom_product"):
            st.success("Custom product added! (Not implemented in backend yet)")
            st.session_state["show_custom_popup"] = False

# --- Search Button ---
if st.button("Discover Products") and query.strip():
    st.session_state["searching"] = True
    st.session_state["products_data"] = None

if st.session_state.get("searching", False):
    with st.spinner("Searching all stores..."):
        try:
            response = requests.post(
                API_URL,
                json={"query": query, "max_per_store": st.session_state["max_entries"]},
                timeout=60,
            )
            response.raise_for_status()
            st.session_state["products_data"] = response.json()
        except Exception as e:
            st.error(f"API error: {e}")
            st.session_state["products_data"] = None
        st.session_state["searching"] = False


products_data = st.session_state.get("products_data", None)
if products_data:
    products_by_store = products_data.get("products", {})
    store_tabs = st.tabs([store.capitalize() for store in products_by_store.keys()])

    # Track selected product per store
    if "selected_products" not in st.session_state:
        st.session_state["selected_products"] = {}

    for idx, (store, products) in enumerate(products_by_store.items()):
        with store_tabs[idx]:
            st.markdown('<div class="scrollable-cards">', unsafe_allow_html=True)

            # 0th index: Add your own product button
            if st.button(f"➕ Add your own product to {store.capitalize()}", key=f"add_{store}_btn", help="Add a custom product link"):
                st.session_state["show_custom_popup"] = True

            if not products:
                st.info(f"No products found for {store.capitalize()}.")
            else:
                # Prepare options and labels for radio
                product_options = [product["id"] for product in products]
                product_labels = [
                    f"{product['name']} (${product['price'] if product['price'] is not None else 'N/A'})"
                    for product in products
                ]
                # Default to first product if nothing selected yet
                selected_id = st.session_state["selected_products"].get(store, product_options[0] if product_options else None)
                selected = st.radio(
                    f"Select a product from {store.capitalize()}",
                    options=product_options,
                    format_func=lambda pid: next((lbl for pid2, lbl in zip(product_options, product_labels) if pid2 == pid), pid),
                    index=product_options.index(selected_id) if selected_id in product_options else 0,
                    key=f"radio_{store}",
                )
                st.session_state["selected_products"][store] = selected

                # Render the cards, highlight the selected one
                for i, product in enumerate(products):
                    is_selected = (product["id"] == selected)
                    card_style = "border: 2px solid #4F8BF9;" if is_selected else "border: 1px solid #eee;"
                    st.markdown(f'<div class="product-card" style="{card_style}">', unsafe_allow_html=True)
                    cols = st.columns([1, 3])
                    with cols[0]:
                        if product.get("image_url"):
                            st.image(product["image_url"], width=100)
                        else:
                            st.write("No image")
                    with cols[1]:
                        st.markdown(
                            f"**[{product['name']}]({product['url']})**"
                        )
                        st.markdown(
                            f"💲 **Price:** ${product['price'] if product['price'] is not None else 'N/A'} &nbsp;&nbsp; "
                            f"⭐ **Rating:** {product.get('rating', 0):.1f} &nbsp;&nbsp; "
                            f"📝 **Reviews:** {product.get('review_count', 0)}"
                        )
                        specs = product.get("specifications", {})
                        if specs:
                            st.markdown(
                                " ".join(
                                    f'<span class="spec-tag">{k}: {v}</span>'
                                    for k, v in specs.items()
                                ),
                                unsafe_allow_html=True,
                            )
                    st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # Continue button
    all_selected = all(
        store in st.session_state["selected_products"] and st.session_state["selected_products"][store]
        for store in products_by_store.keys()
    )
    if st.button("Continue", disabled=not all_selected):
        st.success("Proceeding with selected products!")
else:
    st.info("Enter a product name and click 'Discover Products' to begin.")