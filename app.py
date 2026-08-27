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

# Forzar tema claro estilo Clever (#F8FAF9 y verdes)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #f6faf7 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #11261d !important;
    }
    
    /* Header */
    .clever-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }
    .clever-logo {
        font-size: 32px;
        font-weight: 800;
        color: #0b6836;
        letter-spacing: -0.8px;
    }
    
    /* Contenedor tipo Tarjeta Clever */
    .clever-box {
        background: #ffffff;
        border-radius: 24px;
        padding: 28px;
        border: 1px solid #e7f0eb;
        box-shadow: 0 4px 20px rgba(0, 40, 20, 0.03);
        margin-bottom: 20px;
    }
    
    .kpi-label {
        font-size: 14px;
        font-weight: 600;
        color: #6a8275;
        margin-bottom: 6px;
    }
    
    .kpi-main-number {
        font-size: 38px;
        font-weight: 800;
        color: #0d2319;
        line-height: 1.1;
    }
    
    .badge-clever {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        background-color: #ddfbe8;
        color: #0b7c3e;
        margin-top: 10px;
    }
    
    .badge-clever.up {
        background-color: #fee4e2;
        color: #b42318;
    }

    /* Filas de la lista de categorías al lado de la dona */
    .cat-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 12px;
        border-radius: 12px;
        margin-bottom: 6px;
        background: #fbfdfc;
        font-size: 14px;
        font-weight: 600;
    }
    .cat-bullet {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    /* Tarjetas de Insights */
    .insight-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 16px 20px;
        border: 1px solid #e7f0eb;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .insight-icon-box {
        background: #ebf9f0;
        font-size: 22px;
        padding: 12px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .insight-tag {
        font-size: 11px;
        font-weight: 700;
        color: #2bb673;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }
    .insight-desc {
        font-size: 14px;
        font-weight: 700;
        color: #1a3327;
        margin-top: 2px;
    }
</style>
""", unsafe_allow_html=True)

# Cargar base de datos
@st.cache_data(ttl=3)
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

# Encabezado estilo Clever
st.markdown("""
<div class="clever-top">
    <div class="clever-logo">Clever <span style="font-size:16px; font-weight:600; color:#2bb673;">• Dashboard</span></div>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.info("👋 Aún no tienes transacciones registradas. Envía tu primer gasto por Telegram.")
    st.stop()

# Manejo de fechas y meses
df["fecha"] = pd.to_datetime(df["fecha"])
df["mes_periodo"] = df["fecha"].dt.to_period("M")

meses_disponibles = sorted(df["mes_periodo"].unique(), reverse=True)
meses_nombres = {p: p.strftime("%B %Y").capitalize() for p in meses_disponibles}

col_mes, _ = st.columns([3, 5])
with col_mes:
    mes_seleccionado = st.selectbox(
        "📅 **Periodo:**",
        options=meses_disponibles,
        format_func=lambda x: meses_nombres[x],
        index=0
    )

df_mes = df[df["mes_periodo"] == mes_seleccionado]
periodo_anterior = mes_seleccionado - 1
df_mes_ant = df[df["mes_periodo"] == periodo_anterior]

gastos_mes = df_mes[df_mes["tipo"] == "Gasto"]["monto"].sum()
ingresos_mes = df_mes[df_mes["tipo"] == "Ingreso"]["monto"].sum()
gastos_mes_ant = df_mes_ant[df_mes_ant["tipo"] == "Gasto"]["monto"].sum() if not df_mes_ant.empty else 0.0

dif_porcentaje = 0.0
if gastos_mes_ant > 0:
    dif_porcentaje = ((gastos_mes - gastos_mes_ant) / gastos_mes_ant) * 100

dias_del_mes = max(df_mes["fecha"].dt.day.max(), 1)
gasto_diario_promedio = gastos_mes / dias_del_mes

# --- PANEL PRINCIPAL: Resumen con Dona integrada & Insights ---
col_izq, col_der = st.columns([5, 4], gap="large")

with col_izq:
    st.markdown(f"""
    <div class="clever-box">
        <div class="kpi-label">Resumen del mes ({meses_nombres[mes_seleccionado]})</div>
        <div class="kpi-main-number">S/ {gastos_mes:,.2f}</div>
        <div>
            <span class="badge-clever {'up' if dif_porcentaje > 0 else ''}">
                {'⬆' if dif_porcentaje > 0 else '⬇'} {abs(dif_porcentaje):.1f}% vs. mes pasado
            </span>
        </div>
        <div style="margin-top: 12px; font-size: 13px; color: #6a8275;">
            Gasto diario promedio: <strong style="color: #11261d;">S/ {gasto_diario_promedio:,.2f}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Desglose de Donut + Lista de Categorías
    df_gastos = df_mes[df_mes["tipo"] == "Gasto"]
    if not df_gastos.empty:
        cat_data = df_gastos.groupby("categoria")["monto"].sum().reset_index()
        cat_data["porcentaje"] = (cat_data["monto"] / gastos_mes) * 100
        cat_data = cat_data.sort_values(by="monto", ascending=False)
        
        colores_hex = ["#006837", "#00874e", "#2bb673", "#5cd094", "#8de4b5", "#bbf1d4", "#d4f7e2"]
        
        c_chart, c_list = st.columns([5, 6])
        with c_chart:
            fig = px.pie(
                cat_data,
                values="monto",
                names="categoria",
                hole=0.68,
                color_discrete_sequence=colores_hex
            )
            fig.update_traces(textinfo='none', hoverinfo='label+percent')
            fig.update_layout(
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                height=210,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
            )
            st.plotly_chart(fig, use_container_width=True)
            
        with c_list:
            for i, row in cat_data.iterrows():
                color_bullet = colores_hex[i % len(colores_hex)]
                st.markdown(f"""
                <div class="cat-row">
                    <div>
                        <span class="cat-bullet" style="background-color: {color_bullet};"></span>
                        <span style="color: #334e40;">{row['categoria']}</span>
                    </div>
                    <div style="text-align: right;">
                        <span style="color: #8c9e94; font-size: 12px; margin-right: 8px;">{row['porcentaje']:.0f}%</span>
                        <span style="color: #11261d;">S/ {row['monto']:,.2f}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

with col_der:
    st.markdown('<div class="kpi-label" style="margin-bottom: 12px;">📊 Insights inteligentes</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-icon-box">📉</div>
        <div>
            <div class="insight-tag">Gastos del mes</div>
            <div class="insight-desc">{'Llevas un ' + f"{abs(dif_porcentaje):.1f}% menos que el mes pasado." if dif_porcentaje <= 0 else 'Llevas un ' + f"{dif_porcentaje:.1f}% más que el mes pasado."}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_gastos.empty:
        top_cat = df_gastos["categoria"].value_counts().index[0]
        conteo_top = df_gastos["categoria"].value_counts().iloc[0]
        st.markdown(f"""
        <div class="insight-card">
            <div class="insight-icon-box">🛍️</div>
            <div>
                <div class="insight-tag">Categoría más frecuente</div>
                <div class="insight-desc">Has hecho {conteo_top} transacciones en <strong>{top_cat}</strong>.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    proyeccion = gasto_diario_promedio * 30
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-icon-box">⏱️</div>
        <div>
            <div class="insight-tag">Proyección de gasto</div>
            <div class="insight-desc">Gastarás aprox. <strong>S/ {proyeccion:,.2f}</strong> a fin de mes.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Tabla de movimientos
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📋 Movimientos del Mes")
df_mostrar = df_mes[["fecha", "descripcion", "categoria", "tipo", "medio", "monto", "moneda"]].copy()
df_mostrar["fecha"] = df_mostrar["fecha"].dt.strftime("%d/%m/%Y %H:%M")
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)