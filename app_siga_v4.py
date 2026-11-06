import os
import json
import streamlit as st

# Importamos la clase del agente adaptada a la Rúbrica Oficial (100% / 10.0 Pts)
from siga_evaluator_agent_v4 import RubricSIGAEvaluatorAgent

st.set_page_config(
    page_title="Evaluador Oficial Proyecto SIGA",
    page_icon="📚",
    layout="wide"
)

# Título y Descripción General
st.title("📚 Sistema Evaluador del Proyecto SIGA")
st.subheader("Auditoría Técnica basada en la Rúbrica Oficial de Evaluación (IFCD0112)")

st.markdown("""
Esta herramienta audita la memoria técnica (`.docx`) del **Proyecto SIGA**, verificando la presencia de 
**código fuente real e implementaciones funcionales**, distribuyendo la calificación en los **7 criterios oficiales**:

---
#### 📊 Criterios y Pesos de Evaluación (Total: 10.0 Puntos)
1. **Sistema Linux/Oracle correctamente configurado y documentado:** 15% (1.5 Pts)
2. **Diseño y normalización de la base de datos (3FN):** 15% (1.5 Pts)
3. **Calidad del SQL/PL-SQL (procedures, triggers, transacciones):** 20% (2.0 Pts)
4. **Diseño orientado a objetos y calidad del código Java:** 20% (2.0 Pts)
5. **Funcionamiento de la capa web:** 10% (1.0 Pt)
6. **Trabajo en equipo y reparto equilibrado de tareas:** 10% (1.0 Pt)
7. **Memoria técnica y desarrollo formal:** 10% (1.0 Pt)
""")

# Carga del documento del alumno
uploaded_file = st.file_uploader(
    "Selecciona la memoria técnica del proyecto (.docx)",
    type=["docx"]
)

if uploaded_file is not None:
    st.success(f"📄 Documento cargado correctamente: **{uploaded_file.name}**")

    if st.button("🚀 Ejecutar Auditoría por Rúbrica"):
        temp_file = "temp_siga_audit.docx"

        # Guardar temporalmente el archivo subido
        with open(temp_file, "wb") as f:
            f.write(uploaded_file.getbuffer())

        try:
            with st.spinner("Analizando código Java, PL/SQL, entorno Linux y estructura del documento..."):
                evaluator = RubricSIGAEvaluatorAgent(temp_file)
                resultado = evaluator.run_evaluation()

            st.markdown("---")

            # Nota Global y Estado (APTO / NO APTO)
            nota = resultado["calificacion_global"]

            if nota >= 5.0:
                st.success(
                    f"### ✅ Calificación Global: {nota:.2f} / 10.00 — **{resultado['resultado']}**"
                )
            else:
                st.error(
                    f"### ❌ Calificación Global: {nota:.2f} / 10.00 — **{resultado['resultado']}**"
                )

            st.markdown("### 💡 Dictamen General del Evaluador")
            st.info(resultado["feedback_alumno"])

            # 🚨 Fallos Críticos
            st.markdown("### 🚨 Fallos Críticos y Penalizaciones")
            if resultado["fallos_criticos"]:
                for fallo in resultado["fallos_criticos"]:
                    st.error(f"• {fallo}")
            else:
                st.success("✔ No se detectaron fallos críticos en la entrega.")

            # ✅ Puntos Fuertes
            st.markdown("### ✅ Puntos Fuertes")
            if resultado["puntos_fuertes"]:
                for fuerte in resultado["puntos_fuertes"]:
                    st.success(f"• {fuerte}")
            else:
                st.write("No se registraron observaciones destacadas.")

            # ⚠️ Áreas de Mejora
            st.markdown("### ⚠️ Áreas de Mejora")
            if resultado["areas_mejora"]:
                for mejora in resultado["areas_mejora"]:
                    st.warning(f"• {mejora}")
            else:
                st.success("✔ No hay observaciones adicionales de mejora.")

            # 📊 Desglose Detallado por los 7 Criterios Oficiales
            st.markdown("### 📊 Desglose por Criterios de la Rúbrica")

            grid_cols = st.columns(2)
            for idx, (nombre_criterio, datos) in enumerate(resultado["desglose_modulos"].items()):
                with grid_cols[idx % 2]:
                    with st.expander(
                        f"📌 {nombre_criterio.replace('_', ' ')} — Nota: {datos['nota']} / {datos['max']} Pts",
                        expanded=True
                    ):
                        st.metric(
                            label="Puntuación Obtenida",
                            value=f"{datos['nota']} / {datos['max']} Pts"
                        )
                        for detalle in datos["detalles"]:
                            if "Correcto" in detalle:
                                st.success(f"✔ {detalle}")
                            elif "FALTANTE" in detalle or "Falta" in detalle:
                                st.error(f"✖ {detalle}")
                            else:
                                st.warning(f"⚠ {detalle}")

            # 📥 Exportar Resultados en JSON
            st.markdown("---")
            col_json, col_btn = st.columns([3, 1])
            with col_btn:
                st.download_button(
                    label="📥 Descargar Informe (JSON)",
                    data=json.dumps(resultado, indent=4, ensure_ascii=False),
                    file_name=f"Informe_Rubrica_{uploaded_file.name}.json",
                    mime="application/json"
                )

            with st.expander("🔧 Ver JSON técnico de resultados"):
                st.json(resultado)

        except Exception as e:
            st.error(f"Ocurrió un error al procesar el archivo: {str(e)}")

        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

else:
    st.info("👋 Sube una memoria técnica en formato `.docx` para iniciar la evaluación.")