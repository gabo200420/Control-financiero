import streamlit as st
import pandas as pd
import plotly.express as px
from database import engine

st.set_page_config(
    page_title="Monitor de Finanzas Personales",
    page_icon="📊",
    layout="wide"
)

# Carga directa y segura de datos
def cargar_datos():
    try:
        df = pd.read_sql("SELECT * FROM transacciones ORDER BY created_at DESC", con=engine)
        if not df.empty:
            df["created_at"] = pd.to_datetime(df["created_at"])
        return df
    except Exception:
        return pd.DataFrame()

df = cargar_datos()

st.title("📊 Monitor de Finanzas Personales")

# Sidebar con Filtros
st.sidebar.header("🔍 Filtros de Búsqueda")

if df.empty:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Balance Neto", "S/. 0.00")
    col2.metric("📈 Total Ingresos", "S/. 0.00")
    col3.metric("📉 Total Gastos", "S/. 0.00")
    col4.metric("🛡️ Tasa de Ahorro", "0.0%")
    st.info("Aún no hay transacciones registradas. Envía tu primer gasto o ingreso por Telegram para ver los datos reflejados.")
else:
    # Filtros laterales
    categorias_disponibles = df["category"].dropna().unique().tolist()
    filtro_cat = st.sidebar.multiselect("Categoría", options=categorias_disponibles, default=categorias_disponibles)

    tipos_disponibles = df["transaction_type"].dropna().unique().tolist()
    filtro_tipo = st.sidebar.multiselect("Tipo", options=tipos_disponibles, default=tipos_disponibles)

    # Filtrar DataFrame
    df_filtrado = df[
        (df["category"].isin(filtro_cat)) &
        (df["transaction_type"].isin(filtro_tipo))
    ]

    # Métricas Principales (KPIs)
    total_ingresos = df[df["transaction_type"] == "Ingreso"]["amount"].sum()
    total_gastos = df[df["transaction_type"] == "Gasto"]["amount"].sum()
    balance_neto = total_ingresos - total_gastos
    tasa_ahorro = ((balance_neto / total_ingresos) * 100) if total_ingresos > 0 else 0.0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Balance Neto", f"S/. {balance_neto:,.2f}")
    col2.metric("📈 Total Ingresos", f"S/. {total_ingresos:,.2f}")
    col3.metric("📉 Total Gastos", f"S/. {total_gastos:,.2f}")
    col4.metric("🛡️ Tasa de Ahorro", f"{tasa_ahorro:.1f}%")

    st.write("---")

    # Gráficos Interactivos
    col_g1, col_g2 = st.columns(2)

    df_gastos = df_filtrado[df_filtrado["transaction_type"] == "Gasto"]

    with col_g1:
        st.subheader("Distribución de Gastos por Categoría")
        if not df_gastos.empty:
            fig_pie = px.pie(
                df_gastos,
                names="category",
                values="amount",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No hay gastos registrados en este filtro.")

    with col_g2:
        st.subheader("Gastos por Método de Pago")
        if not df_gastos.empty:
            fig_bar = px.bar(
                df_gastos.groupby("payment_method")["amount"].sum().reset_index(),
                x="payment_method",
                y="amount",
                color="payment_method",
                labels={"payment_method": "Método", "amount": "Monto (S/.)"}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Sin registros de métodos de pago.")

    # Tabla de Movimientos
    st.subheader("📋 Historial de Transacciones")
    st.dataframe(
        df_filtrado[["id", "created_at", "transaction_type", "category", "amount", "currency", "payment_method", "description"]],
        use_container_width=True,
        hide_index=True
    )
    