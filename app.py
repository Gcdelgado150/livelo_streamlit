"""Google-authenticated Streamlit preferences editor for Livelo monitoring."""

from __future__ import annotations

import streamlit as st

from google_sheets import (
    app_setup_message,
    app_workbooks,
    approved_emails,
    read_watchlists,
    save_watchlist,
    worksheet_names_from_secrets,
)


# Snapshot of the partner links listed on Livelo's 200+ partner page.
# Refresh this catalog when Livelo adds, removes, or renames partners.
PARTNER_SLUGS = (
    "mercado-livre", "shopee", "magalu", "decolar", "renner", "booking",
    "beleza-na-web", "carrefour", "cea", "netshoes", "centauro", "o-boticario",
    "fast-shop", "riachuelo", "natura", "farmacias-app", "drogaria-sao-paulo",
    "hoteis", "aliexpress", "pet-love", "insider-store", "carrefour-shopping",
    "camicado", "petz", "nike", "drogarias-pacheco", "localiza", "hering",
    "sams-club", "dafiti", "epoca-cosmeticos", "clickbus", "avon", "sephora",
    "eudora", "decathlon", "movida", "midea", "claro", "sams-club-e-commerce",
    "live-oficial", "angeloni", "havaianas", "abc-da-construcao", "reserva",
    "rentcars", "olympikus", "amobeleza", "kabum", "adcos", "beto-carrero",
    "hope", "buser", "consorcio-magalu", "coffee-mais", "crocs", "abelha-rainha",
    "mizuno", "unidas", "granado", "bagaggio", "tim", "vivara", "posthaus",
    "assist-card-seguros", "under-armour", "asics", "morana", "quem-disse-berenice",
    "loungerie", "max-titanium", "gocase", "allianz", "new-balance",
    "loccitane-au-bresil", "bibi-calcados", "puket", "mondaine", "dudalina", "beep",
    "democrata", "fila", "colcci", "lelis", "converse", "pneu-store", "truss",
    "elbo", "seculus", "sulamerica-seguro-viagem", "samsonite", "loccitane",
    "faber-castell", "easy-live", "zeedog", "malwee", "osklen", "zattini", "edp",
    "bobo", "foco", "mistral", "tokio-marine", "seus-ingressos", "ciclic",
    "seguro-viagem-bradesco", "localiza-assinatura", "guess", "cafe-orfeu", "tia-sonia",
    "john-john", "o.u.i-paris", "gazin", "imaginarium", "forever-liss", "oceane",
    "probiotica", "quero-passagem", "mycon", "hertz-internacional", "lacoste",
    "beach-park", "technos", "mobills", "supernosso", "liz", "beach-park-ingressos",
    "meia-sola", "buddha-spa", "hope-resort", "studioz", "portallar", "bulbe",
    "liga-vitoria", "coris", "salinas", "montecarlo", "individual",
    "bombay-herbse-spices", "localiza-internacional", "cestas-michelli", "giuliana-flores",
    "speedo", "divvino", "cartao-de-todos", "fossil", "hot-beach", "ellus", "avis",
    "cruzeiros-agaxtur", "tripchip", "horas-magicas", "euro", "portoseguro", "medsenior",
    "zee.now", "embracon", "shoestock", "piatan-natural", "umbro", "lego", "grupo-dreams",
    "hering-outlet", "budget", "sulamerica-seguro-odonto", "bradesco-capitalizacao",
    "universal-assistance", "summerville", "dufrio", "travelex", "acer", "nars", "baianao",
    "alura", "shiseido", "ciclic-celular", "beyoung", "oxford", "estapar", "bobstore",
    "luxury-loyalty", "zissou", "portal-das-malas", "yvy", "cabana-magazine", "reserve-car",
    "thule", "qcompra", "sixt", "mapfre", "hero", "vr-collezioni", "coliseu", "quero-quero",
    "bankei", "cook-eletroraro", "mobifacil", "wise-up", "klubi-viagem", "trocafy", "top-moveis",
    "spicy", "klubi-auto", "klabin", "next", "creditas", "maltacor", "pado", "liga-vitoria-auto",
    "hero-seguro-celular", "liga-vitoria-viagem", "perfec-tdraft", "scudoo", "max-racer",
    "home-angels", "oficina", "liga-vitoria-residencial", "klubi-imovel", "mapfre-residencial",
    "suhai", "klubi-moto", "liga-vitoria-moto", "assinatura-coffemais",
    "bradesco-consorcios", "carters", "civitatis", "clube-bancorbras", "drogal", "electrolux",
    "klubi-celular", "loja-do-mecanico", "lojas-torra", "olx", "pet-love-saude", "porto-servico",
    "telhanorte", "casas-bahia", "pontofrio", "extra", "airport-park", "american-tourister",
    "aramis", "brastemp", "nespresso", "ourocap", "shein", "xtrem",
)

PARTNER_LABEL_OVERRIDES = {
    "abc-da-construcao": "ABC da Construcao",
    "amobeleza": "AMOBELEZA",
    "bobo": "BO.BO",
    "cea": "CEA",
    "epoca-cosmeticos": "Epoca Cosmeticos",
    "hoteis": "Hoteis.com",
    "kabum": "KaBuM!",
    "live-oficial": "LIVE!",
    "loccitane": "L'Occitane",
    "loccitane-au-bresil": "L'Occitane au Bresil",
    "o-boticario": "O Boticario",
    "o.u.i-paris": "O.U.i Paris",
    "sams-club": "Sam's Club",
    "sams-club-e-commerce": "Sam's Club E-commerce",
    "zeedog": "Zee.Dog",
    "zee.now": "Zee.Now",
}

PARTNER_OPTIONS = dict(sorted(
    (
        PARTNER_LABEL_OVERRIDES.get(slug, slug.replace("-", " ").title()),
        slug,
    )
    for slug in PARTNER_SLUGS
))
PARTNER_LABEL_BY_SLUG = {slug.casefold(): label for label, slug in PARTNER_OPTIONS.items()}


st.set_page_config(page_title="Livelo partner monitor", page_icon="💠")
st.title("Livelo partner monitor")
st.caption("Sign in with Google to manage your daily email watchlist.")

if not st.user.is_logged_in:
    st.write("Sign in with your Google account. Access is available to approved email addresses.")
    if st.button("Continue with Google", type="primary"):
        st.login()
    st.stop()

email = str(st.user.get("email", "")).strip().casefold()
email_verified = st.user.get("email_verified", False)
if not email or not (email_verified is True or str(email_verified).casefold() == "true"):
    st.error("Google did not provide a verified email address for this account.")
    if st.button("Sign out"):
        st.logout()
    st.stop()

if st.button("Sign out", key="signout"):
    st.logout()

try:
    access_book, preferences_book = app_workbooks(st.secrets)
    users_sheet, preferences_sheet = worksheet_names_from_secrets(st.secrets)
    if email not in approved_emails(access_book, users_sheet):
        st.error("This Google account is not approved yet. Contact the Livelo monitor owner.")
        st.stop()
    watchlists = read_watchlists(preferences_book, preferences_sheet)
    partners = watchlists.get(email, [])
except Exception as exc:
    st.error(app_setup_message())
    st.exception(exc)
    st.stop()

st.write(f"Signed in as **{email}**")
st.subheader("Your monitored partners")
st.write("Your email will contain the shared Top 10 plus the rates for these partners.")

existing_partners = {value.casefold() for value in partners}
available_partners = {
    label: value
    for label, value in PARTNER_OPTIONS.items()
    if value.casefold() not in existing_partners
}

if available_partners:
    with st.form("add_partner", clear_on_submit=True):
        selected_label = st.selectbox(
            "Choose a partner",
            options=["Select a partner", *available_partners],
        )
        add_submit = st.form_submit_button("Add partner")

    if add_submit:
        if selected_label == "Select a partner":
            st.error("Choose a partner from the list.")
        else:
            candidate = available_partners[selected_label]
            try:
                save_watchlist(preferences_book, preferences_sheet, email, [*partners, candidate])
                st.rerun()
            except Exception as exc:
                st.error(f"Could not save your watchlist: {exc}")
else:
    st.info("You have added all partners currently available in the selection list.")

if not partners:
    st.info("Your watchlist is empty. Add a partner above.")
for name in partners:
    column, action = st.columns([5, 1])
    column.write(PARTNER_LABEL_BY_SLUG.get(name.casefold(), name.replace("-", " ").title()))
    if action.button("Remove", key=f"remove-{name}"):
        try:
            save_watchlist(
                preferences_book, preferences_sheet, email,
                [value for value in partners if value.casefold() != name.casefold()],
            )
            st.rerun()
        except Exception as exc:
            st.error(f"Could not update your watchlist: {exc}")
