import streamlit as st
import pandas as pd
import io
from datetime import date, datetime
import re

st.set_page_config(page_title="Altas de Empleados", layout="wide")

st.title("📋 Gestión de Altas de Empleados")

ZONAS = ["Barcelona", "Inca", "Palma", "Madrid", "Toledo", "Gran Canarias"]
RESPONSABLES = ["Camila", "Edgar", "Cesar", "Leomar", "Wilson"]
HORAS_OPTIONS = ["40H", "30H", "20H", "10H"]

st.sidebar.header("⚙️ Configuración global")
responsable = st.sidebar.selectbox("Alta solicitada por (responsable)", RESPONSABLES)
zona_global = st.sidebar.selectbox("Zona por defecto", ZONAS)
horas_global = st.sidebar.selectbox("Horas por defecto", HORAS_OPTIONS)
fecha_global = st.sidebar.date_input("Fecha de inicio por defecto", value=date.today())


st.sidebar.markdown("---")
st.sidebar.caption("Horas, fecha de inicio y zona se pueden ajustar por persona.")

uploaded = st.file_uploader("Sube el CSV de lista de espera", type=["csv"])

def clean_iban(v):
    return re.sub(r"\s+", "", str(v)).upper() if pd.notna(v) and str(v).strip() else ""

def clean_nss(v):
    return re.sub(r"[-\s]", "", str(v)).strip() if pd.notna(v) and str(v).strip() else ""

def parse_csv(file):
    df = pd.read_csv(file, encoding="utf-8-sig", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    col_map = {}
    for c in df.columns:
        cl = c.lower().replace(" ", "").replace("_", "")
        if cl in ("fecha", "date") and "nacimiento" not in cl:
            col_map[c] = "fecha_registro"
        elif "nombre" in cl or "apellido" in cl:
            col_map[c] = "nombre"
        elif "documento" in cl or "dni" in cl or "nie" in cl or "nrodedocumento" in cl:
            col_map[c] = "nie_dni"
        elif "seguridad" in cl or "nss" in cl or "seguridadsocial" in cl:
            col_map[c] = "nss"
        elif "nacimiento" in cl:
            col_map[c] = "fecha_nacimiento"
        elif "email" in cl or "correo" in cl:
            col_map[c] = "correo"
        elif "iban" in cl:
            col_map[c] = "iban"
        elif "nacional" in cl:
            col_map[c] = "nacionalidad"
        elif "vehiculo" in cl or "vehículo" in cl:
            col_map[c] = "herramientas"
    df = df.rename(columns=col_map)
    if "fecha_registro" in df.columns:
        df = df.drop(columns=["fecha_registro"])
    if "iban" in df.columns:
        df["iban"] = df["iban"].apply(clean_iban)
    if "nss" in df.columns:
        df["nss"] = df["nss"].apply(clean_nss)
    for col in ["nombre", "nie_dni", "nss", "fecha_nacimiento", "correo", "iban", "nacionalidad", "herramientas"]:
        if col not in df.columns:
            df[col] = ""
    df = df.fillna("")
    return df

def render_table_html(row, horas, fecha_inicio, zona, resp, table_id="tabla"):
    fields = [
        ("Nombre y apellido:", row.get("nombre", "")),
        ("NIE O DNI", row.get("nie_dni", "")),
        ("N SS", row.get("nss", "")),
        ("Fecha de nacimiento:", row.get("fecha_nacimiento", "")),
        ("Nacionalidad:", row.get("nacionalidad", "")),
        ("Horas:", horas),
        ("Herramientas:", row.get("herramientas", "")),
        ("Zona:", zona),
        ("Para iniciar:", fecha_inicio),
        ("Alta solicitada por:", resp),
        ("Correo electrónico:", row.get("correo", "")),
        ("IBAN bancario:", row.get("iban", "")),
    ]
    rows_html = "".join(
        f"<tr>"
        f"<td style='font-weight:bold;background:#f0f0f0;padding:5px 10px;border:1px solid #000;width:45%'>{label}</td>"
        f"<td style='padding:5px 10px;border:1px solid #000'>{val}</td>"
        f"</tr>"
        for label, val in fields
    )
    return (
        f"<table id='{table_id}' border='1' cellpadding='5' cellspacing='0' "
        f"style='border-collapse:collapse;font-family:Arial,sans-serif;font-size:13px;width:100%'>"
        f"{rows_html}</table>"
    )

COPY_JS = """
<script>
function copyTable(tableId) {
    const table = document.getElementById(tableId);
    const range = document.createRange();
    range.selectNode(table);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
    try {
        document.execCommand('copy');
        const btn = document.getElementById('btn_' + tableId);
        if (btn) {
            btn.innerText = '✅ ¡Copiado! Pégalo en el correo';
            btn.style.background = '#e6f4ea';
            btn.style.borderColor = '#34a853';
            setTimeout(() => {
                btn.innerText = '📋 Copiar tabla';
                btn.style.background = '#fff';
                btn.style.borderColor = '#ccc';
            }, 2500);
        }
    } catch(e) { alert('No se pudo copiar: ' + e); }
    window.getSelection().removeAllRanges();
}
</script>
"""

def copy_button_html(table_id):
    return (
        f"<button id='btn_{table_id}' onclick='copyTable(\"{table_id}\")' "
        f"style='margin-bottom:10px;padding:7px 18px;font-size:13px;cursor:pointer;"
        f"border:1px solid #ccc;border-radius:6px;background:#fff;font-family:Arial;"
        f"transition:all 0.2s'>"
        f"📋 Copiar tabla</button>"
    )

if uploaded:
    df = parse_csv(uploaded)
    total = len(df)
    st.success(f"✅ {total} personas cargadas")

    st.markdown("---")
    st.subheader("Personas en lista de espera")

    if "overrides" not in st.session_state:
        st.session_state.overrides = {}

    for i, row in df.iterrows():
        nombre = row.get("nombre", f"Persona {i+1}") or f"Persona {i+1}"
        key_prefix = f"p{i}"

        with st.expander(f"👤 {nombre}", expanded=False):
            col_info, col_edit = st.columns([1, 1])

            with col_info:
                st.markdown("**Datos del CSV**")
                st.write(f"**NIE/DNI:** {row.get('nie_dni','')}")
                st.write(f"**NSS:** {row.get('nss','')}")
                st.write(f"**F. Nacimiento:** {row.get('fecha_nacimiento','')}")
                st.write(f"**Nacionalidad:** {row.get('nacionalidad','')}")
                st.write(f"**Correo:** {row.get('correo','')}")
                st.write(f"**IBAN:** {row.get('iban','')}")
                st.write(f"**Herramientas:** {row.get('herramientas','')}")

            with col_edit:
                st.markdown("🟠 **Campos a completar**")
                horas = st.selectbox("Horas", HORAS_OPTIONS,
                                     index=HORAS_OPTIONS.index(horas_global),
                                      key=f"{key_prefix}_horas")
                fecha_inicio = st.date_input("Fecha de inicio", value=fecha_global, key=f"{key_prefix}_fecha", value=date.today())
                zona_persona = st.selectbox(
                    "Zona", ZONAS, key=f"{key_prefix}_zona",
                    index=ZONAS.index(zona_global) if zona_global in ZONAS else 0
                )

                st.session_state.overrides[i] = {
                    "horas": horas,
                    "fecha_inicio": fecha_inicio.strftime("%d/%m/%Y"),
                    "zona": zona_persona,
                }

            st.markdown("**Vista previa — pulsa el botón para copiar y pegar en el correo:**")
            ov = st.session_state.overrides.get(i, {})
            table_id = f"tabla_{i}"
            html_table = render_table_html(
                row,
                horas=ov.get("horas", HORAS_OPTIONS[0]),
                fecha_inicio=ov.get("fecha_inicio", ""),
                zona=ov.get("zona", zona_global),
                resp=responsable,
                table_id=table_id,
            )

            st.components.v1.html(
                COPY_JS + copy_button_html(table_id) + html_table,
                height=370,
                scrolling=False,
            )

    st.markdown("---")
    st.subheader("📤 Exportar todos los cuadros")

    col_btn1, col_btn2 = st.columns([1, 1])

    with col_btn1:
        if st.button("Generar HTML con todas las tablas", type="primary"):
            all_html = (
                "<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'>"
                "<title>Altas de Empleados</title>"
                "<style>body{font-family:Arial,sans-serif;padding:30px}"
                ".persona{margin-bottom:40px;page-break-inside:avoid}"
                "h2{font-size:16px;margin-bottom:8px;color:#333}</style></head><body>"
                f"<h1 style='font-size:20px;margin-bottom:30px;'>"
                f"Altas de Empleados — {datetime.now().strftime('%d/%m/%Y %H:%M')}</h1>"
            )
            for i, row in df.iterrows():
                nombre = row.get("nombre", f"Persona {i+1}") or f"Persona {i+1}"
                ov = st.session_state.overrides.get(i, {})
                table = render_table_html(
                    row,
                    horas=ov.get("horas", HORAS_OPTIONS[0]),
                    fecha_inicio=ov.get("fecha_inicio", ""),
                    zona=ov.get("zona", zona_global),
                    resp=responsable,
                    table_id=f"t{i}",
                )
                all_html += f'<div class="persona"><h2>{nombre}</h2>{table}</div>\n'
            all_html += "</body></html>"

            st.download_button(
                label="⬇️ Descargar HTML",
                data=all_html.encode("utf-8"),
                file_name=f"altas_{datetime.now().strftime('%Y%m%d_%H%M')}.html",
                mime="text/html",
            )
            st.success("Abre el HTML en el navegador, selecciona cada tabla y cópiala al correo.")

    with col_btn2:
        if st.button("Exportar resumen Excel"):
            rows_export = []
            for i, row in df.iterrows():
                ov = st.session_state.overrides.get(i, {})
                rows_export.append({
                    "Nombre": row.get("nombre",""),
                    "NIE/DNI": row.get("nie_dni",""),
                    "NSS": row.get("nss",""),
                    "F. Nacimiento": row.get("fecha_nacimiento",""),
                    "Nacionalidad": row.get("nacionalidad",""),
                    "Horas": ov.get("horas", HORAS_OPTIONS[0]),
                    "Herramientas": row.get("herramientas",""),
                    "Zona": ov.get("zona", zona_global),
                    "Para iniciar": ov.get("fecha_inicio",""),
                    "Alta solicitada por": responsable,
                    "Correo": row.get("correo",""),
                    "IBAN": row.get("iban",""),
                })
            df_export = pd.DataFrame(rows_export)
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df_export.to_excel(writer, index=False, sheet_name="Altas")
            st.download_button(
                label="⬇️ Descargar Excel",
                data=buf.getvalue(),
                file_name=f"altas_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

else:
    st.info("👆 Sube el CSV para comenzar. La columna de fecha de registro se ignora automáticamente.")
    st.markdown("""
**Columnas detectadas automáticamente:**
- `nombreYApellido` → Nombre
- `nroDeDocumento` → NIE/DNI
- `nroDeSeguridadSocial` → NSS
- `fechaDeNacimientos` → Fecha de nacimiento
- `email` → Correo
- `IBAN` → IBAN
- `nacionalidad` → Nacionalidad
- `Vehiculo` → Herramientas

La columna `fecha` (timestamp del formulario) se **ignora automáticamente**.
""")