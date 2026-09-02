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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    .stApp {
        background-color: #f6faf7 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #11261d !important;
    }
    
    .clever-top {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .clever-logo {
        font-size: 32px;
        font-weight: 800;
        color: #0b6836;
        letter-spacing: -0.8px;
    }
    
    /* Tarjetas de Métricas Principales */
    .kpi-container {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    }
    .kpi-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 20px 24px;
        border: 1px solid #e7f0eb;
        box-shadow: 0 4px 16px rgba(0, 40, 20, 0.03);
    }
    .kpi-label {
        font-size: 13px;
        font-weight: 600;
        color: #6a8275;
        margin-bottom: 4px;
    }
    .kpi-val {
        font-size: 28px;
        font-weight: 800;
        line-height: 1.2;
    }
    .kpi-val.ingreso { color: #0b7c3e; }
    .kpi-val.gasto { color: #b42318; }
    .kpi-val.balance { color: #11261d; }

    /* Tarjetas de Sección */
    .clever-box {
        background: #ffffff;
        border-radius: 24px;
        padding: 24px;
        border: 1px solid #e7f0eb;
        box-shadow: 0 4px 20px rgba(0, 40, 20, 0.03);
        margin-bottom: 20px;
    }
    
    /* Filas de categorías */
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
    
    /* Insights Cards */
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

    /* Filas de Pagos Fijos / Suscripciones */
    .sub-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        background: #ffffff;
        border-radius: 14px;
        border: 1px solid #eef3f0;
        margin-bottom: 10px;
    }
    .sub-name {
        font-weight: 700;
        font-size: 15px;
        color: #1a3327;
    }
    .sub-date {
        font-size: 12px;
        color: #798e82;
        margin-top: 2px;
    }
    .sub-badge-paid {
        background-color: #ddfbe8;
        color: #0b7c3e;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
    .sub-badge-pending {
        background-color: #f1f5f9;
        color: #64748b;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }
</style>
""", unsafe_allow_html=True)

# 1. Función para eliminar transacciones
def eliminar_transaccion(transaccion_id: int):
    db = SessionLocal()
    try:
        registro = db.query(Transaccion).filter(Transaccion.id == transaccion_id).first()
        if registro:
            db.delete(registro)
            db.commit()
            st.success(f"✅ Transacción #{transaccion_id} eliminada con éxito.")
            st.cache_data.clear()
            st.rerun()
        else:
            st.warning("No se encontró el registro seleccionado.")
    except Exception as e:
        st.error(f"Error al eliminar: {e}")
    finally:
        db.close()

# 2. Cargar datos
@st.cache_data(ttl=2)
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

# Encabezado
st.markdown("""
<div class="clever-top">
    <div class="clever-logo">Clever <span style="font-size:16px; font-weight:600; color:#2bb673;">• Dashboard</span></div>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.info("👋 Aún no tienes transacciones registradas. Envía tu primer mensaje o audio por Telegram.")
    st.stop()

# Manejo de meses
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
balance_neto = ingresos_mes - gastos_mes

gastos_mes_ant = df_mes_ant[df_mes_ant["tipo"] == "Gasto"]["monto"].sum() if not df_mes_ant.empty else 0.0

dif_gastos = 0.0
if gastos_mes_ant > 0:
    dif_gastos = ((gastos_mes - gastos_mes_ant) / gastos_mes_ant) * 100

dias_del_mes = max(df_mes["fecha"].dt.day.max(), 1)
gasto_diario_promedio = gastos_mes / dias_del_mes

# --- 1. TARJETAS DE INGRESOS, GASTOS Y BALANCE ---
st.markdown(f"""
<div class="kpi-container">
    <div class="kpi-card">
        <div class="kpi-label">🟢 Total Ingresos ({meses_nombres[mes_seleccionado]})</div>
        <div class="kpi-val ingreso">S/ {ingresos_mes:,.2f}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">🔴 Total Gastos ({meses_nombres[mes_seleccionado]})</div>
        <div class="kpi-val gasto">S/ {gastos_mes:,.2f}</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-label">💰 Balance Neto</div>
        <div class="kpi-val balance" style="color: {'#0b7c3e' if balance_neto >= 0 else '#b42318'};">S/ {balance_neto:,.2f}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 2. CATEGORÍAS & INSIGHTS ---
col_izq, col_der = st.columns([5, 4], gap="large")

with col_izq:
    st.markdown('<div class="clever-box">', unsafe_allow_html=True)
    st.markdown('<div class="kpi-label" style="font-size:16px; margin-bottom:15px; color:#11261d;">🏷️ Desglose de Gastos por Categoría</div>', unsafe_allow_html=True)
    
    df_gastos = df_mes[df_mes["tipo"] == "Gasto"]
    if not df_gastos.empty:
        cat_data = df_gastos.groupby("categoria")["monto"].sum().reset_index()
        cat_data["porcentaje"] = (cat_data["monto"] / gastos_mes) * 100 if gastos_mes > 0 else 0
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
    else:
        st.write("No hay gastos registrados en este periodo.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_der:
    st.markdown('<div class="kpi-label" style="margin-bottom: 12px;">📊 Insights inteligentes</div>', unsafe_allow_html=True)
    
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-icon-box">📉</div>
        <div>
            <div class="insight-tag">Comparativa mensual</div>
            <div class="insight-desc">{'Gastaste un ' + f"{abs(dif_gastos):.1f}% menos que el mes pasado." if dif_gastos <= 0 else 'Gastaste un ' + f"{dif_gastos:.1f}% más que el mes pasado."}</div>
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
            <div class="insight-tag">Proyección de gasto mensual</div>
            <div class="insight-desc">Gastarás aprox. <strong>S/ {proyeccion:,.2f}</strong> a fin de mes.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- 3. DETECTOR DE PAGOS FIJOS / SUSCRIPCIONES (Estilo Clever) ---
st.markdown('<div class="clever-box">', unsafe_allow_html=True)
st.markdown('### 🔄 Pagos Fijos y Suscripciones del Mes')
st.caption("Detección automática de servicios y pagos mensuales recurrentes:")

# Lista de suscripciones y servicios a monitorear (puedes ajustar o agregar más fácilmente)
SERVICIOS_FIJOS = [
    {"nombre": "Spotify", "palabras": ["spotify"], "dia_estimado": 5, "monto_aprox": 15.90, "icono": "🎵"},
    {"nombre": "Netflix", "palabras": ["netflix"], "dia_estimado": 10, "monto_aprox": 28.90, "icono": "🎬"},
    {"nombre": "Internet / Telefonía", "palabras": ["internet", "movistar", "claro", "entel", "win", "plan"], "dia_estimado": 20, "monto_aprox": 65.00, "icono": "🌐"},
    {"nombre": "Luz / Electricidad", "palabras": ["luz", "enel", "luz del sur", "electrosur", "electronorte", "ensa"], "dia_estimado": 25, "monto_aprox": 85.00, "icono": "⚡"},
    {"nombre": "Agua / Sedapal", "palabras": ["agua", "sedapal", "epsel"], "dia_estimado": 28, "monto_aprox": 35.00, "icono": "💧"},
    {"nombre": "ChatGPT / OpenAI", "palabras": ["openai", "chatgpt"], "dia_estimado": 15, "monto_aprox": 75.00, "icono": "🤖"}
]

col_sub1, col_sub2 = st.columns(2)

for i, serv in enumerate(SERVICIOS_FIJOS):
    col = col_sub1 if i % 2 == 0 else col_sub2
    
    # Buscar si existe alguna transacción en este mes que coincida con este servicio
    pago_detectado = None
    for _, fila in df_mes.iterrows():
        desc = str(fila["descripcion"]).lower()
        if any(p in desc for p in serv["palabras"]):
            pago_detectado = fila
            break
    
    with col:
        if pago_detectado is not None:
            dia_pago = pd.to_datetime(pago_detectado["fecha"]).strftime("%d/%m")
            st.markdown(f"""
            <div class="sub-row">
                <div>
                    <div class="sub-name">{serv['icono']} {serv['nombre']}</div>
                    <div class="sub-date">Pagado el {dia_pago}</div>
                </div>
                <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                    <strong style="color: #11261d;">S/ {pago_detectado['monto']:,.2f}</strong>
                    <span class="sub-badge-paid">✔ Pagado</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="sub-row">
                <div>
                    <div class="sub-name">{serv['icono']} {serv['nombre']}</div>
                    <div class="sub-date">Día estimado: {serv['dia_estimado']} de cada mes</div>
                </div>
                <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                    <span style="color: #8c9e94;">~S/ {serv['monto_aprox']:,.2f}</span>
                    <span class="sub-badge-pending">⏳ Pendiente</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# --- 4. HISTORIAL DE MOVIMIENTOS ---
st.markdown("### 📋 Movimientos del Mes")

df_mostrar = df_mes[["id", "fecha", "descripcion", "categoria", "tipo", "medio", "monto", "moneda"]].copy()
# Restar 5 horas para convertir de UTC a hora local de Perú
df_mostrar["fecha"] = (pd.to_datetime(df_mostrar["fecha"]) - pd.Timedelta(hours=5)).dt.strftime("%d/%m/%Y %H:%M")
st.dataframe(df_mostrar, use_container_width=True, hide_index=True)

# Sección para Eliminar Transacciones Erróneas
with st.expander("🗑️ **Eliminar un importe equivocado**"):
    st.write("Selecciona una transacción de la lista para eliminarla permanentemente de la base de datos:")
    
    opciones_dict = {
        f"ID #{row['id']} | {row['fecha']} | {row['tipo']}: {row['descripcion']} - S/ {row['monto']:,.2f}": row['id']
        for _, row in df_mostrar.iterrows()
    }
    
    if opciones_dict:
        seleccion_label = st.selectbox("Movimiento a eliminar:", options=list(opciones_dict.keys()))
        col_btn1, col_btn2 = st.columns([2, 5])
        with col_btn1:
            if st.button("🗑️ Eliminar Registro", type="primary", use_container_width=True):
                id_seleccionado = opciones_dict[seleccion_label]
                eliminar_transaccion(id_seleccionado)
    else:
        st.write("No hay movimientos registrados en este mes.")