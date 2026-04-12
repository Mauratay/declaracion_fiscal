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
import os
import glob
from PIL import Image
import pytesseract
import xml.etree.ElementTree as ET

def extraer_texto_archivo(archivo):
    texto_completo = ""
    nombre = getattr(archivo, 'name', str(archivo)).lower()

    try:
        if nombre.endswith('.pdf'):
            with pdfplumber.open(archivo) as pdf:
                for pagina in pdf.pages:
                    texto_extraido = pagina.extract_text()
                    if texto_extraido:
                        texto_completo += texto_extraido + "\n"
        elif nombre.endswith(('.png', '.jpg', '.jpeg')):
            img = Image.open(archivo)
            texto_completo = pytesseract.image_to_string(img)
        elif nombre.endswith('.xml'):
            if isinstance(archivo, str):
                with open(archivo, 'r', encoding='utf-8') as f:
                    contenido = f.read()
            else:
                archivo.seek(0)
                contenido = archivo.read().decode('utf-8')
            
            texto_completo = contenido
            
            try:
                root = ET.fromstring(contenido)
                
                for elem in root.iter():
                    if 'Descripcion' in elem.attrib:
                        texto_completo += f"\nDescripción: {elem.attrib['Descripcion']}\n"
                    if 'Nombre' in elem.attrib:
                        texto_completo += f"\nNombre: {elem.attrib['Nombre']}\n"
                        
                    if 'FechaPago' in elem.attrib:
                        fecha_val = elem.attrib['FechaPago']
                        if len(fecha_val) >= 10:
                            f = fecha_val[:10].split('-')
                            if len(f) >= 3:
                                texto_completo += f"\nFecha de pago {f[2]}/{f[1]}/{f[0]}\n"
                                
                    if 'Fecha' in elem.attrib:
                        fecha_val = elem.attrib['Fecha']
                        if len(fecha_val) >= 10:
                            f = fecha_val[:10].split('-')
                            if len(f) >= 3:
                                texto_completo += f"\nFecha {f[2]}/{f[1]}/{f[0]}\n"
                    
                    if 'TotalSueldos' in elem.attrib:
                        texto_completo += f"\nTotal percepciones {elem.attrib['TotalSueldos']}\n"
                    elif 'TotalPercepciones' in elem.attrib:
                        texto_completo += f"\nTotal percepciones {elem.attrib['TotalPercepciones']}\n"
                        
                    if 'TotalImpuestosRetenidos' in elem.attrib:
                        texto_completo += f"\nTotal impuestos retenidos {elem.attrib['TotalImpuestosRetenidos']}\n"

                total = root.get('Total')
                if total:
                    texto_completo += f"\nTotal final factura médica o escolar: {total}\n"
                    
            except Exception:
                pass
        else:
            st.warning(f"Formato no soportado: {nombre}")
            
    except Exception as e:
        nombre_err = getattr(archivo, 'name', str(archivo))
        st.error(f"Error en la lectura del archivo {nombre_err}: {e}")
        
    return texto_completo

def procesar_documentos(archivos, anio_declaracion):
    datos_extraidos = []
    
    patron_fecha_pago = re.compile(r"Fecha de pago[\"\,\:\s]*([\d]{2}/[\d]{2}/[\d]{4}|[\d]{4}-[\d]{2}-[\d]{2})", re.IGNORECASE)
    patron_fecha_general = re.compile(r"Fecha[\"\,\:\s]*([\d]{2}/[\d]{2}/[\d]{4}|[\d]{4}-[\d]{2}-[\d]{2})", re.IGNORECASE)
    patron_ingreso = re.compile(r"Total percepciones[\"\,\s]*([\d,]+\.\d{2})", re.IGNORECASE)
    patron_isr = re.compile(r"Total impuestos retenidos[\"\,\s]*([\d,]+\.\d{2})", re.IGNORECASE)
    patron_cifra_monetaria = re.compile(r"\$?\s*([\d,]+\.\d{2})")
    
    patron_escolar = re.compile(r"(colegiatura|escuela|colegio|instituto|universidad|escolar|educativ[oa]|preescolar|primaria|secundaria|preparatoria|bachillerato|instEducativas)", re.IGNORECASE)

    for archivo in archivos:
        texto = extraer_texto_archivo(archivo)
        
        match_fecha_pago = patron_fecha_pago.search(texto)
        match_fecha_general = patron_fecha_general.search(texto)
        match_fecha = match_fecha_pago if match_fecha_pago else match_fecha_general
        
        match_ingreso = patron_ingreso.search(texto)
        match_isr = patron_isr.search(texto)
        
        nombre_archivo = getattr(archivo, 'name', os.path.basename(archivo) if isinstance(archivo, str) else str(archivo))

        # Validación del año
        fecha = "No identificada"
        if match_fecha:
            fecha_str = match_fecha.group(1)
            try:
                if "/" in fecha_str:
                    anio_doc = int(fecha_str.split("/")[-1])
                elif "-" in fecha_str:
                    anio_doc = int(fecha_str.split("-")[0])
                else:
                    anio_doc = None
            except:
                anio_doc = None

            if anio_doc and anio_doc != anio_declaracion:
                st.warning(f"Se ignoró '{nombre_archivo}' porque corresponde al año {anio_doc} y no a la declaración del {anio_declaracion}.")
                continue
            
            fecha = fecha_str

        # Una Nómina debe tener explícitamente "Total percepciones" o la palabra "nómina" en su texto.
        # Las facturas médicas pueden tener retenciones de ISR (pasando match_isr) por honorarios.
        es_nomina = bool(match_ingreso) or ("nómina" in texto.lower()) or ("nomina" in texto.lower())

        if es_nomina:
            # Es un recibo de Nómina
            ingreso = float(match_ingreso.group(1).replace(",", "")) if match_ingreso else 0.0
            isr = float(match_isr.group(1).replace(",", "")) if match_isr else 0.0

            datos_extraidos.append({
                "Tipo": "Nómina", 
                "Archivo": nombre_archivo, 
                "Fecha": fecha, 
                "Ingresos": ingreso, 
                "ISR Retenido": isr, 
                "Deducciones Médicas": 0.0,
                "Deducciones Escolares": 0.0
            })
        else:
            # Es una Factura Médica, Escolar (u otro gasto)
            todas_las_cifras = patron_cifra_monetaria.findall(texto)
            
            if todas_las_cifras:
                ultima_cifra = todas_las_cifras[-1]
                total_factura = float(ultima_cifra.replace(",", ""))
                
                es_escolar = patron_escolar.search(texto)
                
                if es_escolar:
                    tipo = "Factura Escolar"
                    ded_medicas = 0.0
                    ded_escolares = total_factura
                else:
                    tipo = "Factura Médica u Otros"
                    ded_medicas = total_factura
                    ded_escolares = 0.0
                    
                datos_extraidos.append({
                    "Tipo": tipo, 
                    "Archivo": nombre_archivo, 
                    "Fecha": fecha, 
                    "Ingresos": 0.0, 
                    "ISR Retenido": 0.0, 
                    "Deducciones Médicas": ded_medicas,
                    "Deducciones Escolares": ded_escolares
                })
            else:
                datos_extraidos.append({
                    "Tipo": "Desconocido (Sin montos)", 
                    "Archivo": nombre_archivo, 
                    "Fecha": fecha, 
                    "Ingresos": 0.0, 
                    "ISR Retenido": 0.0, 
                    "Deducciones Médicas": 0.0,
                    "Deducciones Escolares": 0.0
                })
            
    return pd.DataFrame(datos_extraidos)

st.set_page_config(page_title="Extractor Fiscal CFDI", layout="wide")
st.title("Extractor de Datos para Declaración Anual")
st.markdown("Esta herramienta se ejecuta localmente. Tus archivos no son enviados a ningún servidor.")

st.header("1. Configuración y Carga de Archivos")

import datetime
anio_actual = datetime.datetime.now().year
col1, col2 = st.columns(2)
with col1:
    anio_declaracion = st.number_input("Año de la declaración fiscal", min_value=2000, max_value=2100, value=anio_actual - 1, step=1)

modo_carga = st.radio("Método de entrada", ["Archivos", "Carpeta Completa"], horizontal=True)

archivos_procesar = []
tipos_permitidos = ["pdf", "xml", "png", "jpg", "jpeg"]

if modo_carga == "Archivos":
    uploaded_files = st.file_uploader("Selecciona o arrastra todos tus documentos fiscales", type=tipos_permitidos, accept_multiple_files=True, key="documentos")
    if uploaded_files:
        archivos_procesar = uploaded_files
else:
    def obtener_archivos_por_extension(ruta):
        archivos = []
        for root_dir, dirs, files in os.walk(ruta):
            for file in files:
                if file.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg', '.xml')):
                    archivos.append(os.path.join(root_dir, file))
        return archivos

    ruta_docs = st.text_input("Ruta de la carpeta local con los documentos", key="ruta_docs")
    if ruta_docs and os.path.isdir(ruta_docs):
        archivos_procesar = obtener_archivos_por_extension(ruta_docs)
        st.success(f"Se detectaron {len(archivos_procesar)} archivos válidos.")
    elif ruta_docs:
        st.error("La ruta especificada no existe o no es una carpeta.")

st.header("2. Confirmación")
confirmacion = st.checkbox("Confirmo que he agregado todos los archivos necesarios para el cálculo.")

if confirmacion:
    if not archivos_procesar:
        st.warning("No se han cargado archivos para procesar.")
    elif st.button("Procesar Archivos"):
        with st.spinner("Extrayendo datos de los documentos..."):
            df_resultados = procesar_documentos(archivos_procesar, anio_declaracion)
            
            st.header("3. Resultados")
            st.dataframe(df_resultados, use_container_width=True)
            
            total_ingresos = df_resultados["Ingresos"].sum()
            total_isr = df_resultados["ISR Retenido"].sum()
            total_medicas = df_resultados["Deducciones Médicas"].sum()
            total_escolares = df_resultados["Deducciones Escolares"].sum()
            
            st.subheader("Resumen")
            col_res1, col_res2, col_res3, col_res4 = st.columns(4)
            col_res1.metric("Total Ingresos", f"${total_ingresos:,.2f}")
            col_res2.metric("Total ISR Retenido", f"${total_isr:,.2f}")
            col_res3.metric("Total Deducciones Médicas", f"${total_medicas:,.2f}")
            col_res4.metric("Total Escolares", f"${total_escolares:,.2f}")
            
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
