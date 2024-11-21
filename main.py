import os
import tkinter as tk
from tkinter import Label
from PIL import Image, ImageTk, ImageSequence
import threading
import openai
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import datetime
import subprocess
import speech_recognition as sr  
import time

# Cargar variables de entorno desde el archivo .env
load_dotenv("C:/Users/juanc/Documents/Assistant/.env")  # Especifica la ruta de tu .env

# Configurar las claves y el endpoint de OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_base = os.getenv("OPENAI_ENDPOINT")
openai.api_type = "azure"
openai.api_version = "2024-08-01-preview"

# Configurar claves del Servicio de Voz de Azure
speech_key = os.getenv("SPEECH_KEY")
service_region = os.getenv("SPEECH_REGION")

# Configurar Speech to Text de Azure para español
speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
speech_config.speech_recognition_language = "es-ES"  # Cambia el idioma a español según tu preferencia
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config)

# Configurar la síntesis de voz (Texto a Voz)
speech_config.speech_synthesis_language = "es-CO"  # Cambiar el idioma de síntesis según tu preferencia
speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config)

# Variable para almacenar el nombre del usuario
nombre_usuario = None

# Crear la ventana principal de Tkinter
ventana = tk.Tk()
ventana.title("Asistente de Voz")

# Rutas de imágenes y GIFs
carita_path = "C:/Users/juanc/Documents/Assistant/images/elmofroz.jpeg"
hablando_gif_path = "C:/Users/juanc/Documents/Assistant/images/elmotalk.gif"

# Crear el canvas para mostrar las imágenes
canvas = tk.Canvas(ventana, width=300, height=300)
canvas.pack()

# Cargar imagen de la carita feliz
carita_image = Image.open(carita_path)
carita_image = carita_image.resize((300, 300), Image.Resampling.LANCZOS)
carita_photo = ImageTk.PhotoImage(carita_image)

# Crear un widget para mostrar la imagen
imagen_label = Label(ventana, image=carita_photo)
imagen_label.pack()

gif_frames = []
gif_index = 0
gif_animation_active = False
imagen_tamano = (300, 300)  # Tamaño fijo para imágenes y GIFs

# Crear un Label para el texto de estado
estado_label = tk.Label(ventana, text="", font=("Arial", 14), fg="black")
estado_label.pack(pady=10)  # Ajustar el margen para que quede separado

def cambiar_estado(texto):
    """
    Cambia el texto del Label que muestra el estado del asistente.
    """
    estado_label.config(text=texto)
    estado_label.update()


def cambiar_imagen(ruta_imagen, es_gif=False, velocidad_ms=50):
    """
    Cambia la imagen o inicia la animación del GIF en la interfaz.

    :param ruta_imagen: Ruta al archivo de imagen o GIF.
    :param es_gif: Booleano que indica si es un GIF animado.
    :param velocidad_ms: Tiempo en milisegundos entre cada frame del GIF.
    """
    global gif_frames, gif_index, gif_animation_active

    if es_gif:
        # Cargar el GIF completo y redimensionar cada frame
        gif = Image.open(ruta_imagen)
        gif_frames = [
            ImageTk.PhotoImage(frame.copy().resize(imagen_tamano, Image.Resampling.LANCZOS))
            for frame in ImageSequence.Iterator(gif)
        ]
        gif_index = 0
        gif_animation_active = True

        def actualizar_gif():
            global gif_index, gif_animation_active
            if gif_animation_active:
                imagen_label.config(image=gif_frames[gif_index])
                gif_index = (gif_index + 1) % len(gif_frames)  # Repetir el GIF
                imagen_label.after(velocidad_ms, actualizar_gif)

        actualizar_gif()
    else:
        # Cargar una imagen estática y redimensionarla
        nueva_imagen = Image.open(ruta_imagen)
        nueva_imagen = nueva_imagen.resize(imagen_tamano, Image.Resampling.LANCZOS)
        nueva_photo = ImageTk.PhotoImage(nueva_imagen)
        imagen_label.config(image=nueva_photo)
        imagen_label.image = nueva_photo
        gif_animation_active = False  # Detener cualquier animación previa

def escuchar_y_convertir():
    """
    Escucha la voz del usuario y convierte el audio a texto usando Azure Speech to Text.
    """
    print("Escuchando...")
    result = speech_recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Texto reconocido: {result.text}")
        return result.text.lower()  # Convertir el texto a minúsculas para comparación
    else:
        print("No se reconoció ninguna voz.")
        return None  # Retorna None si no se reconoció voz



def generar_respuesta(prompt):
    """
    Genera una respuesta desde OpenAI usando el prompt proporcionado.
    """
    try:
        response = openai.ChatCompletion.create(
            engine="gpt-35-turbo",  
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=100
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return str(e)  # Retornar el error como string si es necesario



def ejecutar_comando(texto):
    """
    Ejecuta comandos específicos del sistema según el texto proporcionado.
    """
    global nombre_usuario
    ruta_documentos = "C:\\Users\\juanc\\Documents"  # Ruta específica para crear y buscar archivos
     # Detectar si el usuario pregunta por su nombre
    if any(phrase in texto for phrase in ["nombre", "quién soy", "quien soy"]):
        if nombre_usuario:
            return f"Te llamas {nombre_usuario}."
        else:
            # Solicitar el nombre del usuario si no está definido
            cambiar_imagen(hablando_gif_path, es_gif=True)
            speech_synthesizer.speak_text_async("¿Cuál es tu nombre?")
            nombre_usuario = escuchar_y_convertir()

            if nombre_usuario:
                saludo = f"Hola, {nombre_usuario}"
                speech_synthesizer.speak_text_async(saludo)
                cambiar_imagen(carita_path)
                return saludo
            else:
                cambiar_imagen(carita_path)
                return "No pude escuchar tu nombre. Por favor, intenta de nuevo."
    elif "hora" in texto:
        hora_actual = datetime.datetime.now().strftime("%H:%M")
        return f"La hora actual es {hora_actual}."
    elif "abrir carpeta" in texto:
        path = "C:\\Users"  # Cambia esta ruta según tus necesidades
        os.startfile(path)
        return f"Abriendo la carpeta en {path}."
    elif "calculadora" in texto:
        subprocess.run("calc.exe", shell=True)
        return "Abriendo la calculadora."
    elif "navegador" in texto or "google chrome" in texto:
        subprocess.run("start chrome", shell=True)
        return "Abriendo Google Chrome."
    elif "youtube" in texto:
        subprocess.run("start chrome www.youtube.com", shell=True)
        return "Abriendo YouTube."
    elif "wikipedia" in texto:
        subprocess.run("start chrome www.wikipedia.org", shell=True)
        return "Abriendo Wikipedia."
    elif "abrir whatsapp" in texto:
        subprocess.run("start whatsapp", shell=True)
        return "Abriendo WhatsApp."
    elif "música" in texto or "musica" in texto:
        # Preguntar al usuario qué canción desea escuchar
        speech_synthesizer.speak_text_async("¿Qué canción deseas escuchar?")
        cancion = escuchar_y_convertir()
        if cancion:
            # Generar URL de búsqueda para Spotify Web
            query = "+".join(cancion.split())  # Formatear la canción para la URL
            url_spotify = f"https://open.spotify.com/search/{query}"
            subprocess.run(f"start chrome {url_spotify}", shell=True)  # Cambia 'chrome' por tu navegador preferido si es necesario
            return f"Buscando y reproduciendo {cancion} en Spotify."
        else:
            return "No pude entender el nombre de la canción. Por favor, intenta de nuevo."
    elif "cómo me llamo" in texto:
        if nombre_usuario:
            return f"Te llamas {nombre_usuario}."
        else:
            return "Aún no me has dicho tu nombre."
    elif "cómo te llamas" in texto:
        return "Me llamo Elmo, tu asistente virtual."
    elif "crear archivo de texto" in texto:
        speech_synthesizer.speak_text_async("¿Cuál es el nombre del archivo que deseas crear?")
        nombre_archivo = escuchar_y_convertir()
        if nombre_archivo:
            ruta_archivo = os.path.join(ruta_documentos, f"{nombre_archivo}.txt")
            with open(ruta_archivo, "w") as archivo:
                archivo.write(f"Este es el archivo {nombre_archivo} creado por Elmo.")
            return f"El archivo {nombre_archivo}.txt ha sido creado en {ruta_documentos}."
        else:
            return "No pude escuchar el nombre del archivo. Por favor, intenta de nuevo."
    elif "abrir archivo de texto" in texto:
        speech_synthesizer.speak_text_async("¿Cuál es el nombre del archivo que deseas abrir?")
        nombre_archivo = escuchar_y_convertir()
        if nombre_archivo:
            ruta_archivo = os.path.join(ruta_documentos, f"{nombre_archivo}.txt")
            if os.path.exists(ruta_archivo):
                os.startfile(ruta_archivo)
                return f"Abriendo el archivo {nombre_archivo}.txt en {ruta_documentos}."
            else:
                return f"No encontré el archivo {nombre_archivo}.txt en {ruta_documentos}."
        else:
            return "No pude escuchar el nombre del archivo que quieres abrir. Por favor, intenta de nuevo."
    elif any(phrase in texto for phrase in ["en que materia estamos", "materia", "como se llama la materia"]):  # Nuevo comando
        return "La materia es Ciencia de Datos"
    elif any(phrase in texto for phrase in ["profesor", "docente", "maestro"]):  # Nuevo comando
        return "El docente es Alfredo Díaz"
    elif any(phrase in texto for phrase in ["creador", "creadores", "quienes te hicieron", "autores", "autor"]):  # Nuevo comando
        return "Fui creado por un grupo de estudiantes de la UNAB de sexto semestre llamados Juan Aguirre, Andrés Parra, Miguel Rueda, Juan Urbina"
    elif any(phrase in texto for phrase in ["adios", "hasta luego", "chao", "me despido"]):  # Nuevo comando
        return "Hasta la próxima"


    return None  # Si no es un comando conocido
 
def manejar_asistente():
    """
    Maneja el flujo del asistente. Alterna entre reposo y escucha activa.
    """
    global nombre_usuario

    # Mensaje de bienvenida (solo se ejecuta la primera vez)
    print("Bienvenido al asistente Elmo.")
    cambiar_imagen(hablando_gif_path, es_gif=True)  # Cambiar al GIF animado
    ventana.update()
    speech_synthesizer.speak_text_async("Bienvenido, soy Elmo, tu asistente virtual")
    ventana.after(4000, lambda: cambiar_imagen(carita_path))  # Volver a la imagen estática después de 3 segundos

    while True:
        # Escuchar en reposo
        print("Esperando palabra clave...")
        cambiar_estado("En reposo... Di 'Elmo' para activarme.")
        ventana.update()

        # Usar Azure para escuchar palabras clave
        palabras_clave = ["elmo", "oye", "hey", "hey elmo", "escucha", "una pregunta", "despierta"]
        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            texto = result.text.lower()  # Convertir texto a minúsculas

            # Verificar si contiene alguna palabra clave
            if any(palabra in texto for palabra in palabras_clave):
                print("Palabra clave detectada.")
                cambiar_estado("Escuchando...")  # Cambiar a modo de escucha activa
                ventana.update()

                # Escuchar activamente y procesar comandos o preguntas
                texto_recibido = escuchar_y_convertir()  # Llama a la función de escucha activa
                cambiar_estado("")  # Limpiar el estado después de escuchar
                ventana.update()

                if texto_recibido:
                    cambiar_imagen(hablando_gif_path, es_gif=True)  # Cambiar al GIF animado
                    ventana.update()

                    # Procesar el comando o pregunta
                    respuesta_comando = ejecutar_comando(texto_recibido)
                    if respuesta_comando:
                        print("Respuesta del asistente (comando):", respuesta_comando)
                        speech_synthesizer.speak_text_async(respuesta_comando)
                        duracion_lectura = calcular_duracion_lectura(respuesta_comando)
                    else:
                        # Generar respuesta usando OpenAI
                        respuesta = generar_respuesta(f"Responde en español: {texto_recibido}")
                        print("Respuesta del asistente:", respuesta)
                        speech_synthesizer.speak_text_async(respuesta)
                        duracion_lectura = calcular_duracion_lectura(respuesta)

                    # Esperar el tiempo calculado antes de volver a la imagen estática
                    ventana.after(duracion_lectura, lambda: cambiar_imagen(carita_path))
        elif result.reason == speechsdk.ResultReason.NoMatch:
            print("No se reconoció ninguna palabra.")
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Cancelación: {cancellation_details.reason}. Detalle: {cancellation_details.error_details}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error en el reconocimiento. Reintentando...")



def calcular_duracion_lectura(texto):
    """
    Calcula la duración estimada para leer el texto en voz alta.
    Asume una velocidad promedio de 2 palabras por segundo.
    """
    palabras = len(texto.split())
    velocidad_palabras_por_segundo = 3  # Ajusta según la velocidad de lectura deseada
    duracion = palabras / velocidad_palabras_por_segundo
    return int(duracion * 1000)  # Retorna el tiempo en milisegundos





# Iniciar el asistente dentro de un hilo
threading.Thread(target=manejar_asistente, daemon=True).start()

# Iniciar la ventana principal
ventana.mainloop()