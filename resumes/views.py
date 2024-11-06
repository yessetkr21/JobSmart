from django.shortcuts import render, redirect, get_object_or_404
from .models import Resume
from vacantes.models import Vacante
from datetime import datetime
import pdfplumber
import openai
import os
from dotenv import load_dotenv


# Create your views here.
def showHomepage(request):
    return render(request,'home.html' )

def leerPdf(pdf_file):
    """Función que utiliza pdfplumber para extraer el texto de un PDF"""
    texto = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            texto += page.extract_text()
    return texto

def uploadResume(request):
    if request.method == 'POST' and request.FILES.get('pdf'):
        pdf_file = request.FILES['pdf']
        texto = leerPdf(pdf_file)

        # Guardar el resumen
        resume = Resume(nombre=pdf_file.name, contenido=texto)
        resume.save()

        # Obtener el vacante_id del formulario
        vacante_id = request.POST.get('vacante_id')

        # Redirigir a la vista resultado con los IDs correspondientes
        return redirect('resultado', resume_id=resume.id, vacante_id=vacante_id)

    # Obtener todas las vacantes para el formulario
    vacantes = Vacante.objects.filter(fecha_cierre__gte=datetime.now())
    return render(request, 'resume.html', {'vacantes': vacantes})

def calcular_nivel_mejora(recomendaciones_aplicadas, total_recomendaciones):
    if total_recomendaciones == 0:
        return 0
    return (recomendaciones_aplicadas / total_recomendaciones) * 100

# Cargar las variables de entorno desde api_key.env
"""_ = load_dotenv('../api_keys.env')

# Obtener la clave de API desde el archivo .env
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    print("Error: la clave de la API de OpenAI no se ha cargado correctamente.")
else:
    print(f"Clave API cargada: {openai.api_key}")"""

openai.api_key = ''

def obtenerRecomendaciones(contenido_cv, vacante):
    """Función que utiliza la API de OpenAI para obtener recomendaciones para el CV"""
    prompt = f"""
    Dada la siguiente descripción de una vacante y el contenido de una hoja de vida, 
    proporciona recomendaciones sobre cómo mejorar la hoja de vida para que se ajuste mejor a la vacante.

    Descripción de la vacante:
    {vacante.descripcion}  # Asumiendo que 'descripcion' es un campo en el modelo Vacante

    Contenido de la hoja de vida:
    {contenido_cv}

    Recomendaciones:
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # Puedes elegir el modelo que prefieras
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500  # Ajusta el número de tokens según sea necesario
        )
        recomendaciones = response['choices'][0]['message']['content']
        return recomendaciones.strip()
    except Exception as e:
        print(f"Error al obtener recomendaciones: {e}")
        return "No se pudieron generar recomendaciones en este momento."

def calcularRelevancia(contenido_cv, vacante): #mostrar el %
    """Función que utiliza la API de OpenAI para calcular la relevancia del CV con respecto a la vacante"""
    prompt = f"""
    Dada la descripción de una vacante y el contenido de un CV, evalúa qué tan relevante es el CV para la vacante 
    en una escala del 0% al 100%. Devuelve solo el porcentaje de relevancia basado en la alineación entre el CV y los requisitos de la vacante.

    Descripción de la vacante:
    {vacante.descripcion}

    Contenido de la hoja de vida:
    {contenido_cv}

    Relevancia:
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10  # Un número pequeño de tokens para solo obtener el porcentaje
        )
        relevancia = response['choices'][0]['message']['content']
        return relevancia.strip()
    except Exception as e:
        print(f"Error al calcular relevancia: {e}")
        return "No se pudo calcular la relevancia en este momento."
def calcularMejora(contenido_cv, recomendaciones):
    """Calcula el porcentaje de mejora en base a las recomendaciones dadas."""
    prompt = f"""
    Basado en el contenido inicial de un CV y las recomendaciones para mejorar, evalúa en qué porcentaje 
    el CV mejoraría si se aplicaran las recomendaciones dadas. Devuelve solo el porcentaje de mejora.

    Contenido original del CV:
    {contenido_cv}

    Recomendaciones para mejorar el CV:
    {recomendaciones}

    Porcentaje de mejora:
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        mejora = response['choices'][0]['message']['content']
        return mejora.strip()
    except Exception as e:
        print(f"Error al calcular mejora: {e}")
        return "No se pudo calcular la mejora en este momento."
def resultado(request, resume_id, vacante_id):
    resume = get_object_or_404(Resume, id=resume_id)
    vacante = get_object_or_404(Vacante, id=vacante_id)

    # Obtener recomendaciones y relevancia
    recomendaciones = obtenerRecomendaciones(resume.contenido, vacante)
    relevancia = calcularRelevancia(resume.contenido, vacante)

    # Calcular mejora
    mejora = calcularMejora(resume.contenido, recomendaciones)

    return render(request, 'resultado.html', {
        'resume': resume,
        'vacante': vacante,
        'recomendaciones': recomendaciones,
        'relevancia': relevancia,
        'mejora': mejora
    })

    
        
