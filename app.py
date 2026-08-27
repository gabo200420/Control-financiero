import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from dotenv import load_dotenv
from database import SessionLocal
from models import Transaccion

load_dotenv()

st.set_page_config(
    page_title="Clever Finance",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilos visuales Clever (Verde & Blanco)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #f7faf8;
        color: #1a2e26;
    }
    
    .clever-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0 20px 0;
    }
    .clever-logo {
        font-size: 30px;
        font-weight: 800;
        color: #0b6836;
        letter-spacing: -0.5px;
    }
    
    .clever-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 50, 20, 0.04);
        border: 1px solid #ebf2ee;
        margin-bottom: 20px;
    }
    
    .kpi-title {
        font-size: 14px;
        font-weight: 600;
        color: #6b7f75;
        margin-bottom: 4px;
    }
    
    .kpi-amount {
        font-size: 34px;
        font-weight: 800;
        color: #11261d;
        margin: 0;
    }
    
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 700;
        background-color: #dcfce7;
        color: #15803d;
        margin-top: 6px;
    }
    
    .badge-pill.negative {
        background-color: #fee2e2;
        color: #b91c1c;
    }
    
    .insight-row {
        background: #ffffff;
        border-radius: 16px;
        padding: 16px 20px;
        border: 1px solid #edf3ef;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .insight-icon {
        background: #eef9f2;
        font-size: 22px;
        padding: 10px;
        border-radius: 12px;
    }
    .insight-text-title {
        font-size: 12px;
        font-weight: 600;
        color: #2bb673;
        margin-bottom: 2px;
    }
    .insight-text-desc {
        font-size: 15px;
        font-weight: 700;
        color: #1b3528;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=5)
def cargar_datos():
    db = SessionLocal()
    try:
        query = db.query(Transaccion).order_by(Transaccion.created_at.desc()).all()
        if not query:
            return pd.DataFrame()
        
        datos = [{
            "id": t.id,
            "monto": float(t.amount),
            "moneda": t.currency,
            "categoria": t.category,
            "tipo": t.transaction_type,
            "medio": t.payment_method,
            "descripcion": t.description,
            "fecha": t.created_at
        } for t in query]
        return pd.DataFrame(datos)
    finally:
        db.close()

df = cargar_datos()

st.markdown("""
<div class="clever-header">
    <div class="clever-logo">Clever <span style="font-size:16px; font-weight:600; color:#2bb673;">• Dashboard</span></div>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.info("👋 Aún no tienes transacciones registradas. Envía tu primer gasto por Telegram.")
    st.stop()

# Manejo de meses
df["fecha"] = pd.to_datetime(df["fecha"])
df["mes_periodo"] = df["fecha"].dt.to_period("M")

meses_disponibles = sorted(df["mes_periodo"].unique(), reverse=True)
meses_nombres = {p: p.strftime("%B %Y").capitalize() for p in meses_disponibles}

col_sel1, col_sel2 = st.columns([2, 4])
with col_sel1:
    mes_seleccionado = st.selectbox(
        "📅 **Filtrar por Mes:**",
        options=meses_disponibles,
        format_func=lambda x: meses_nombres[x],
        index=0
    )

# Filtrado por mes actual y anterior
df_mes = df[df["mes_periodo"] == mes_seleccionado]
periodo_anterior = mes_seleccionado - 1
df_mes_ant = df[df["mes_periodo"] == periodo_anterior]

gastos_mes = df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum()
ingresos_mes = df_mes[df_mes["tipo"] == "Ingreso"]["monto"].sum()
gastos_mes_ant = df_mes_ant[df_mes_ant["tipo"] == "Gasto"]["monto"].sum() if not df_mes_ant.empty else 0.0

dif_porcentaje = 0.0
if gastos_mes_ant > 0:
    dif_porcentaje = ((gastos_mes - gastos_mes_ant) / gastos_mes_ant) * 100

dias_en_mes = df_mes["fecha"].dt.day.max() if not df_mes.empty else 1
gasto_diario_promedio = gastos_mes / max(dias_en_mes, 1)

# Estructura principal
col_resumen, col_insights = st.columns([3, 2], gap="large")

with col_resumen:
    st.markdown(f"""
    <div class="clever-card">
        <div class="kpi-title">Resumen del mes ({meses_nombres[mes_seleccionado]})</div>
        <div class="kpi-amount">S/ {gastos_mes:,.2f}</div>
        <div>
            <span class="badge-pill {'negative' if dif_porcentaje > 0 else ''}">
                {'⬆' if dif_porcentaje > 0 else '⬇'} {abs(dif_porcentaje):.1f}% vs. mes pasado
            </span>
        </div>
        <div style="margin-top: 15px; font-size: 13px; color: #6b7f75;">
            Gasto diario promedio: <strong style="color:#11261d;">S/ {gasto_diario_promedio:,.2f}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    df_gastos = df_mes[df_mes["tipo"] == "Gasto"]
    if not df_gastos.empty:
        cat_data = df_gastos.groupby("categoria")["monto"].sum().reset_index()
        cat_data = cat_data.sort_values(by="monto", ascending=False)
        
        paleta_verde = ["#006837", "#00874e", "#2bb673", "#5cd094", "#8de4b5", "#bbf1d4"]
        
        fig = px.pie(
            cat_data,
            values="monto",
            names="categoria",
            hole=0.65,
            color_discrete_sequence=paleta_verde
        )
        fig.update_traces(
            textposition='inside',
            textinfo='percent',
            hovertemplate="<b>%{label}</b><br>S/ %{value:,.2f}<br>(%{percent})<extra></extra>"
        )
        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
            margin=dict(t=10, b=10, l=10, r=10),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig, use_container_width=True)

with col_insights:
    st.markdown('<div class="kpi-title" style="margin-bottom: 12px;">📊 Insights del Mes</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="insight-row">
        <div class="insight-icon">📉</div>
        <div>
            <div class="insight-text-title">Gastos del mes</div>
            <div class="insight-text-desc">{'Llevas un ' + f"{abs(dif_porcentaje):.1f}% menos que el mes pasado." if dif_porcentaje <= 0 else 'Llevas un ' + f"{dif_porcentaje:.1f}% más que el mes pasado."}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_gastos.empty:
        top_cat = df_gastos["categoria"].value_counts().index[0]
        conteo_top = df_gastos["categoria"].value_counts().iloc[0]
        st.markdown(f"""
        <div class="insight-row">
            <div class="insight-icon">🛍️</div>
            <div>
                <div class="insight-text-title">Categoría más frecuente</div>
                <div class="insight-text-desc">Has hecho {conteo_top} transacciones en <strong>{top_cat}</strong>.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    proyeccion = gasto_diario_promedio * 30
    st.markdown(f"""
    <div class="insight-row">
        <div class="insight-icon">⏱️</div>
        <div>
            <div class="insight-text-title">Proyección de gasto</div>
            <div class="insight-text-desc">Gastarás aprox. <strong>S/ {proyeccion:,.2f}</strong> a fin de mes.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Lista detallada de transacciones
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Historial del Mes")
df_mostrar = df_mes[["fecha", "descripcion", "categoria", "tipo", "medio", "monto", "moneda"]].copy()
df_mostrar["fecha"] = df_mostrar["fecha"].dt.strftime("%d/%m/%Y %H:%M")
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)