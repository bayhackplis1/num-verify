import streamlit as st
import phonenumbers
from phone_analyzer import AdvancedPhoneAnalyzer
from social_checker import SocialChecker
from utils import format_phone_number, create_result_df
import pandas as pd

st.set_page_config(
    page_title="Analizador Avanzado de Números Telefónicos",
    page_icon="📱",
    layout="wide"
)

def main():
    st.title("📱 Analizador Avanzado de Números Telefónicos")

    # Sidebar con información
    with st.sidebar:
        st.markdown("""
        ### 🔍 Características
        - Análisis detallado de números
        - Verificación en múltiples redes sociales
        - Detección de spam y riesgo
        - Información de operador y ubicación
        - Búsqueda inversa
        """)

    # Input del número telefónico
    phone_input = st.text_input(
        "Ingresa un número telefónico (formato internacional con código de país)",
        placeholder="Ejemplo: +34612345678"
    )

    if phone_input:
        try:
            # Validación básica del número
            parsed_number = phonenumbers.parse(phone_input, None)
            if not phonenumbers.is_valid_number(parsed_number):
                st.error("❌ El número ingresado no es válido")
                return

            formatted_number = format_phone_number(parsed_number)

            with st.spinner("Analizando número..."):
                # Análisis del número
                analyzer = AdvancedPhoneAnalyzer(formatted_number)
                carrier_details = analyzer.get_carrier_details()  # Usando get_carrier_details en lugar de get_basic_info

                # Verificación de redes sociales
                social_checker = SocialChecker(formatted_number)
                social_presence = social_checker.check_social_presence()

                # Mostrar resultados en pestañas
                tab1, tab2, tab3 = st.tabs(["📋 Información del Operador", "🔍 Datos Adicionales", "🌐 Redes Sociales"])

                with tab1:
                    st.subheader("Información del Operador")
                    carrier_info = carrier_details["carrier_info"]
                    st.dataframe(create_result_df({
                        "Operador": carrier_info.name,
                        "Tipo de Red": carrier_info.network_type,
                        "Región": carrier_info.region,
                        "Estado": "Activo" if carrier_info.active else "Inactivo",
                        "Nivel de Riesgo": carrier_info.risk_level.value,
                        "Score de Verificación": f"{carrier_info.verification_score}/100"
                    }), use_container_width=True)

                with tab2:
                    st.subheader("Información Adicional y Análisis")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Detalles Técnicos")
                        technical_info = carrier_details["additional_info"]["red_info"]
                        st.dataframe(create_result_df(technical_info), use_container_width=True)
                    with col2:
                        st.markdown("#### Análisis de Riesgo")
                        risk_info = carrier_details["additional_info"]["seguridad"]
                        st.dataframe(create_result_df(risk_info), use_container_width=True)

                with tab3:
                    st.subheader("Presencia en Redes Sociales")
                    # Organizar redes sociales en grupos
                    messaging_apps = {k:v for k,v in social_presence.items() if k in ["WhatsApp", "Telegram", "Viber"]}
                    social_networks = {k:v for k,v in social_presence.items() if k not in ["WhatsApp", "Telegram", "Viber"]}

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("#### Apps de Mensajería")
                        st.dataframe(create_result_df(messaging_apps), use_container_width=True)
                    with col2:
                        st.markdown("#### Redes Sociales")
                        st.dataframe(create_result_df(social_networks), use_container_width=True)

        except Exception as e:
            st.error(f"❌ Error al procesar el número: {str(e)}")

    st.markdown("---")
    st.markdown("""
    ### ℹ️ Acerca de esta herramienta
    - Utiliza múltiples fuentes de datos para un análisis completo
    - Verifica la presencia en redes sociales de forma respetuosa
    - Analiza patrones de riesgo y calidad del número
    - Los resultados pueden variar según la disponibilidad de datos

    ⚠️ Nota: Esta herramienta respeta la privacidad y solo utiliza datos públicamente accesibles
    """)

if __name__ == "__main__":
    main()
