# MIT License
# Copyright (c) 2026
# 
# Se concede permiso, de forma gratuita, a cualquier persona que obtenga una copia
# de este software y de los archivos de documentación asociados (el "Software"), para
# utilizar el Software sin restricción, incluyendo sin limitación los derechos
# de usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar, y/o vender
# copias del Software, y para permitir a las personas a las que se les proporcione el
# Software a hacer lo mismo, sujeto a las siguientes condiciones:
# 
# El aviso de copyright anterior y este aviso de permiso se incluirán en todas
# las copias o partes sustanciales del Software.
# 
# EL SOFTWARE SE PROPORCIONA "TAL CUAL", SIN GARANTÍA DE NINGÚN TIPO.

import streamlit as st
import pdfplumber
import re
import pandas as pd

def extraer_texto_pdf(archivo_en_memoria):
    texto_completo = ""
    try:
        with pdfplumber.open(archivo_en_memoria) as pdf:
            for pagina in pdf.pages:
                texto_extraido = pagina.extract_text()
                if texto_extraido:
                    texto_completo += texto_extraido + "\n"
    except Exception as e:
        st.error(f"Error en la lectura del archivo {archivo_en_memoria.name}: {e}")
    return texto_completo

def procesar_documentos(archivos_nomina, archivos_medicos):
    datos_extraidos = []
    
    patron_fecha = re.compile(r"Fecha de pago[\"\,\s]*([\d]{2}/[\d]{2}/[\d]{4})", re.IGNORECASE)
    patron_ingreso = re.compile(r"Total percepciones[\"\,\s]*([\d,]+\.\d{2})", re.IGNORECASE)
    patron_isr = re.compile(r"Total impuestos retenidos[\"\,\s]*([\d,]+\.\d{2})", re.IGNORECASE)
    patron_cifra_monetaria = re.compile(r"\$?\s*([\d,]+\.\d{2})")

    for archivo in archivos_nomina:
        texto = extraer_texto_pdf(archivo)
        
        match_fecha = patron_fecha.search(texto)
        match_ingreso = patron_ingreso.search(texto)
        match_isr = patron_isr.search(texto)

        fecha = match_fecha.group(1) if match_fecha else "No identificada"
        ingreso = float(match_ingreso.group(1).replace(",", "")) if match_ingreso else 0.0
        isr = float(match_isr.group(1).replace(",", "")) if match_isr else 0.0

        datos_extraidos.append({
            "Tipo": "Nómina", 
            "Archivo": archivo.name, 
            "Fecha": fecha, 
            "Ingresos": ingreso, 
            "ISR Retenido": isr, 
            "Deducciones Médicas": 0.0
        })

    for archivo in archivos_medicos:
        texto = extraer_texto_pdf(archivo)
        todas_las_cifras = patron_cifra_monetaria.findall(texto)
        
        if todas_las_cifras:
            ultima_cifra = todas_las_cifras[-1]
            total_factura = float(ultima_cifra.replace(",", ""))
            datos_extraidos.append({
                "Tipo": "Factura Médica", 
                "Archivo": archivo.name, 
                "Fecha": "N/A", 
                "Ingresos": 0.0, 
                "ISR Retenido": 0.0, 
                "Deducciones Médicas": total_factura
            })
        else:
            datos_extraidos.append({
                "Tipo": "Factura Médica (Error)", 
                "Archivo": archivo.name, 
                "Fecha": "N/A", 
                "Ingresos": 0.0, 
                "ISR Retenido": 0.0, 
                "Deducciones Médicas": 0.0
            })
            
    return pd.DataFrame(datos_extraidos)

st.set_page_config(page_title="Extractor Fiscal CFDI", layout="wide")
st.title("Extractor de Datos para Declaración Anual")
st.markdown("Esta herramienta se ejecuta localmente. Tus archivos no son enviados a ningún servidor.")

st.header("1. Carga de Archivos")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Recibos de Nómina")
    archivos_nomina = st.file_uploader("Selecciona o arrastra los PDF de nómina", type="pdf", accept_multiple_files=True, key="nomina")

with col2:
    st.subheader("Facturas Médicas")
    archivos_medicos = st.file_uploader("Selecciona o arrastra los PDF de facturas médicas", type="pdf", accept_multiple_files=True, key="medicas")

st.header("2. Confirmación")
confirmacion = st.checkbox("Confirmo que he agregado todos los archivos necesarios para el cálculo.")

if confirmacion:
    if not archivos_nomina and not archivos_medicos:
        st.warning("No se han cargado archivos para procesar.")
    elif st.button("Procesar Archivos"):
        with st.spinner("Extrayendo datos de los documentos..."):
            df_resultados = procesar_documentos(archivos_nomina, archivos_medicos)
            
            st.header("3. Resultados")
            st.dataframe(df_resultados, use_container_width=True)
            
            total_ingresos = df_resultados["Ingresos"].sum()
            total_isr = df_resultados["ISR Retenido"].sum()
            total_medicas = df_resultados["Deducciones Médicas"].sum()
            
            st.subheader("Resumen")
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric("Total Ingresos", f"${total_ingresos:,.2f}")
            col_res2.metric("Total ISR Retenido", f"${total_isr:,.2f}")
            col_res3.metric("Total Deducciones Médicas", f"${total_medicas:,.2f}")
            
            csv = df_resultados.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Descargar reporte en CSV",
                data=csv,
                file_name='reporte_fiscal.csv',
                mime='text/csv',
            )

st.divider()

st.header("Guía: Pasos para presentar la Declaración Anual")
st.markdown("""
Los pasos requeridos para ejecutar el trámite ante la autoridad fiscal son los siguientes:

1. **Acceso al portal del SAT:** Durante el mes de abril, ingresa a la plataforma del Servicio de Administración Tributaria en el apartado de "Declaración Anual de Personas Físicas". Es necesario autenticarte con tu Registro Federal de Contribuyentes (RFC) y tu Contraseña o firma electrónica (e.firma) ([SAT - Personas Físicas](https://www.gob.mx/sat/acciones-y-programas/personas-fisicas-144637)).
2. **Revisión de ingresos y retenciones:** Compara la información precargada en el aplicativo con los totales generados en el reporte de esta herramienta (Ingresos e ISR retenido) para auditar que la suma sea exacta ([BBVA - Cómo hacer la declaración de impuestos](https://www.bbva.mx/educacion-financiera/impuestos/como-hacer-la-declaracion-de-impuestos.html)).
3. **Validación de deducciones personales:** Navega a la pestaña de deducciones personales y verifica que todas tus facturas médicas estén listadas. El sistema aplicará los topes legales de deducción de forma automática ([Scotiabank - Cómo se hace la declaración anual](https://www.scotiabank.com.mx/blog/para-ti/como-se-hace-la-declaracion-anual-de-impuestos)).
4. **Cálculo de impuestos:** Revisa la liquidación final elaborada por el sistema. El resultado indicará si existe un saldo a favor que puedes recuperar o un impuesto a cargo que debes solventar ([Taxdown - Declaración anual por primera vez](https://taxdown.com.mx/declaracion-anual/declaracion-anual-por-primera-vez)).
5. **Envío de la declaración:** Para solicitar la devolución de un saldo a favor, captura una cuenta CLABE interbancaria a tu nombre. En caso de impuesto a cargo, descarga la línea de captura para ejecutar el pago mediante la banca en línea. Firma el documento y conserva el acuse de recibo con sello digital ([Procedimiento de declaración anual - YouTube](https://www.youtube.com/watch?v=UsPY7HWMGB8)).
""")