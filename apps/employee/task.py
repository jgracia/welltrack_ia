from celery import shared_task
from celery.exceptions import Ignore
from django.http import HttpResponse
import base64

import os
import cv2
from collections import defaultdict
import time
from deepface import DeepFace
from datetime import datetime
from django.conf import settings

from .models import EmotionAnalysis

'''
@shared_task(bind=True)
def analyze_video_task(self, video_id):
    try:
        total_steps = 5
        current_step = 0

        # Paso 1: Obtener ruta del video
        video_obj = EmotionAnalysis.objects.get(pk=video_id)
        video_path = os.path.join(settings.MEDIA_ROOT, video_obj.video_file.name)
        # print("Video Path: ", video_path)

        current_step += 1
        self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})
        
        # Paso 2: Obtener inicializar
        print("\n=> Paso: %s inicializando parámetros => Porcentaje: %s" %(current_step, ((current_step / total_steps) * 100) ))
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        aggregated_emotions = defaultdict(float)
        frame_count = 0
        valid_frame_count = 0
        dominant_frame = None
        dominant_emotion = None
        start_time = time.time()  # Tiempo de inicio

        current_step += 1
        self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})
        
        # Paso 3: Analizando
        print("\n=> Paso: %s analizando video => Porcentaje: %s" %(current_step, ((current_step / total_steps) * 100) ))
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if frame_count % 30 == 0:  # Procesar cada 30 cuadros (aproximadamente 1 segundo a 30 fps)
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'])
                    if isinstance(result, list):
                        for face in result:
                            if 'emotion' in face:
                                for emotion, score in face['emotion'].items():
                                    aggregated_emotions[emotion] += score
                                valid_frame_count += 1
                                # Verificar si este frame tiene la emoción dominante
                                current_dominant_emotion = max(face['emotion'], key=face['emotion'].get)
                                if dominant_emotion is None or face['emotion'][current_dominant_emotion] > face['emotion'][dominant_emotion]:
                                    dominant_emotion = current_dominant_emotion
                                    dominant_frame = frame
                    else:
                        aggregated_emotions['error'] = 'Unexpected result structure'
                except Exception as e:
                    aggregated_emotions['error'] = str(e)
            frame_count += 1

        current_step += 1
        self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})
        
        # Paso 4: Procesando resultados
        print("\n=> Paso: %s procesando resultados => Porcentaje: %s" %(current_step, ((current_step / total_steps) * 100) ))
        end_time = time.time()  # Tiempo de fin
        duration = end_time - start_time  # Duración en segundos

        cap.release()

        # Calcular el promedio de las emociones
        if valid_frame_count > 0:
            for emotion in aggregated_emotions:
                aggregated_emotions[emotion] /= valid_frame_count
            dominant_emotion = max(aggregated_emotions, key=aggregated_emotions.get)
        else:
            aggregated_emotions = {'error': 'No valid frames processed'}
            dominant_emotion = 'unknown'

        analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result_summary = {
            'emotions': aggregated_emotions,
            'dominant_emotion': dominant_emotion
        }

        current_step += 1
        self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})
        
        # Paso 5: Actualizar emociones en db
        print("\n=> Paso: %s actualizando db => Porcentaje: %s" %(current_step, ((current_step / total_steps) * 100) ))
        video_obj.emotions_detected = result_summary  
        video_obj.save()
        current_step += 1
        self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})

        # Paso : Devolviendo parametros
        print("\n=> Paso: %s devolviendo parametros => Porcentaje: %s" %(current_step, ((current_step / total_steps) * 100) ))
        current_step += 1
        self.update_state(state='PROGRESS', meta={'percent': 100})  # Finalizar al 100%
        print("\n=> Paso: %s fin proceso => Porcentaje: %s" %(current_step, ((current_step / total_steps) * 100) ))

        return {
            "result_summary": result_summary,
            "analysis_time": analysis_time,
            "dominant_emotion": dominant_emotion,
            "frame_count": frame_count,
            "duration": duration
        }

    except ValueError as ve:
        print(f"Error el análisis de video: {ve}")
        self.update_state(state='FAILURE', meta={'error': f'{type(ve).__name__}: {str(ve)}'})
        raise ve

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        self.update_state(state='FAILURE', meta={'error': f'{type(e).__name__}: {str(e)}'})
        raise e
'''

'''
@shared_task(bind=True)
def analyze_video_task(self, video_id):
    try:
        # Inicializar progreso
        current_step = 0
        total_steps = 50  # Número de pasos que consideras dentro del ciclo

        # Paso 1: Obtener ruta del video
        video_obj = EmotionAnalysis.objects.get(pk=video_id)
        video_path = os.path.join(settings.MEDIA_ROOT, video_obj.video_file.name)

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        total_steps = max(1, total_frames // 30)  # Evitar dividir por 0, usar al menos 1 paso

        current_step = 0
        self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})

        # Paso 2: Inicializar parámetros
        aggregated_emotions = defaultdict(float)
        frame_count = 0
        valid_frame_count = 0
        dominant_frame = None
        dominant_emotion = None
        start_time = time.time()  # Tiempo de inicio

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 30 == 0:  # Procesar cada 30 cuadros
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'])
                    if isinstance(result, list):
                        for face in result:
                            if 'emotion' in face:
                                for emotion, score in face['emotion'].items():
                                    aggregated_emotions[emotion] += score
                                valid_frame_count += 1
                                # Verificar si este frame tiene la emoción dominante
                                current_dominant_emotion = max(face['emotion'], key=face['emotion'].get)
                                if dominant_emotion is None or face['emotion'][current_dominant_emotion] > face['emotion'][dominant_emotion]:
                                    dominant_emotion = current_dominant_emotion
                                    dominant_frame = frame
                    else:
                        aggregated_emotions['error'] = 'Unexpected result structure'
                except Exception as e:
                    aggregated_emotions['error'] = str(e)

                # Actualizar progreso sin superar el 100%
                #current_step += 1
                #self.update_state(state='PROGRESS', meta={'percent': round((current_step / total_steps) * 100, 2)})

                # Actualiza el progreso dentro del ciclo, pero no al 100%
                current_step += 1
                progress = (current_step / total_steps) * 90  # Máximo 90%
                self.update_state(state='PROGRESS', meta={'percent': progress})
                print(f"\n=> Paso: {current_step} analizando video => Porcentaje: {progress}%")

            frame_count += 1

        # Paso 3: Procesando resultados
        step = 0
        additional_steps = 2
        end_time = time.time()  # Tiempo de fin
        duration = end_time - start_time  # Duración en segundos
        cap.release()

        # Actualizar el progreso después del ciclo while
        step += 1
        progress = 90 + (step / additional_steps) * 10  # Completar hasta 100%
        self.update_state(state='PROGRESS', meta={'percent': progress})
        print("=> Paso adicional 1: %s" % progress)

        # Calcular el promedio de las emociones
        if valid_frame_count > 0:
            for emotion in aggregated_emotions:
                aggregated_emotions[emotion] /= valid_frame_count
            dominant_emotion = max(aggregated_emotions, key=aggregated_emotions.get)
        else:
            aggregated_emotions = {'error': 'No valid frames processed'}
            dominant_emotion = 'unknown'

        print("=>xxxxxxxxxxxxxxxxxxxxx")
        analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result_summary = {
            'emotions': aggregated_emotions,
            'dominant_emotion': dominant_emotion
        }

        print("=>************************************")

        # Actualizar el progreso después del ciclo while
        step += 1
        progress = 90 + (step / additional_steps) * 10  # Completar hasta 100%
        self.update_state(state='PROGRESS', meta={'percent': progress})
        print("=> Paso adicional 2: %s" % progress)

        # Paso 4: Actualizar emociones en la base de datos
        #video_obj.emotions_detected = result_summary  
        #video_obj.save()

        # Finalmente, actualiza el progreso al 100% solo cuando toda la tarea haya terminado
        self.update_state(state='PROGRESS', meta={'percent': 100})
        print(f"\n=> Paso: {total_steps} fin proceso => Porcentaje: 100%")

        return {
            "result_summary": result_summary,
            "analysis_time": analysis_time,
            "dominant_emotion": dominant_emotion,
            "frame_count": frame_count,
            "duration": duration
        }

    except ValueError as ve:
        error_message = f'{type(ve).__name__}: {str(ve)}'
        self.update_state(state='FAILURE', meta={'error': error_message})
        raise Ignore()

    except Exception as e:
        error_message = f'{type(e).__name__}: {str(e)}'
        self.update_state(state='FAILURE', meta={'error': error_message})
        raise Ignore()
'''

'''
@shared_task(bind=True)
def analyze_video_task(self, video_id):
    try:
        # Paso 1: Inicialización y configuración
        video_obj = EmotionAnalysis.objects.get(pk=video_id)
        video_path = os.path.join(settings.MEDIA_ROOT, video_obj.video_file.name)

        # Inicializar progreso
        self.update_state(state='PROGRESS', meta={'percent': 5})  # 5% de progreso

        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Paso 2: Preparación y setup
        aggregated_emotions = defaultdict(float)
        frame_count = 0
        valid_frame_count = 0
        dominant_frame = None
        dominant_emotion = None
        start_time = time.time()  # Tiempo de inicio

        # Actualizar al 20% al terminar el setup
        self.update_state(state='PROGRESS', meta={'percent': 20})
        
        # Paso 3: Procesamiento del video dentro del ciclo `while`
        current_step = 0
        max_steps = total_frames // 30  # Total de cuadros a procesar
        if max_steps == 0:
            max_steps = 1  # Evitar dividir por cero

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 30 == 0:  # Procesar cada 30 cuadros
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'])
                    if isinstance(result, list):
                        for face in result:
                            if 'emotion' in face:
                                for emotion, score in face['emotion'].items():
                                    aggregated_emotions[emotion] += score
                                valid_frame_count += 1
                                current_dominant_emotion = max(face['emotion'], key=face['emotion'].get)
                                if dominant_emotion is None or face['emotion'][current_dominant_emotion] > face['emotion'][dominant_emotion]:
                                    dominant_emotion = current_dominant_emotion
                                    dominant_frame = frame
                except Exception as e:
                    aggregated_emotions['error'] = str(e)

                # Actualiza el progreso dentro del ciclo
                current_step += 1
                progress = 20 + (current_step / max_steps) * 70  # Progreso entre 20% y 90%
                self.update_state(state='PROGRESS', meta={'percent': progress})
                print(f"\n=> Paso: {current_step} analizando video => Porcentaje: {progress}%")

            frame_count += 1

        cap.release()

        # Paso 4: Procesar los resultados después del ciclo `while`
        if valid_frame_count > 0:
            for emotion in aggregated_emotions:
                aggregated_emotions[emotion] /= valid_frame_count
            dominant_emotion = max(aggregated_emotions, key=aggregated_emotions.get)
        else:
            aggregated_emotions = {'error': 'No valid frames processed'}
            dominant_emotion = 'unknown'

        # Completar el progreso restante al 100%
        self.update_state(state='PROGRESS', meta={'percent': 100})
        print("=> Finalizando análisis: Progreso 100%")

        analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result_summary = {
            'emotions': aggregated_emotions,
            'dominant_emotion': dominant_emotion
        }

        return {
            "result_summary": result_summary,
            "analysis_time": analysis_time,
            "dominant_emotion": dominant_emotion,
            "frame_count": frame_count,
            "duration": time.time() - start_time  # Duración en segundos
        }

    except ValueError as ve:
        error_message = f'{type(ve).__name__}: {str(ve)}'
        self.update_state(state='FAILURE', meta={'error': error_message})
        raise Ignore()

    except Exception as e:
        error_message = f'{type(e).__name__}: {str(e)}'
        self.update_state(state='FAILURE', meta={'error': error_message})
        raise Ignore()
'''


@shared_task(bind=True)
def analyze_video_task(self, video_id):
    try:
        # Paso 1: Obtener ruta del video
        video_obj = EmotionAnalysis.objects.get(pk=video_id)
        video_path = os.path.join(settings.MEDIA_ROOT, video_obj.video_file.name)

        # Inicializar progreso
        self.update_state(state='PROGRESS', meta={'percent': 5})  # 5% de progreso

        # Paso 2: Inicialización
        cap = cv2.VideoCapture(video_path)
        
        # Actualizar el progreso al 10%
        self.update_state(state='PROGRESS', meta={'percent': 10})  # 10% de progreso

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        aggregated_emotions = defaultdict(float)
        frame_count = 0
        valid_frame_count = 0
        dominant_frame = None
        dominant_emotion = None
        start_time = time.time()  # Tiempo de inicio

        # Actualizar al 15% al terminar la inicialización
        self.update_state(state='PROGRESS', meta={'percent': 15})

        # Paso 3: Procesamiento del video dentro del ciclo `while`
        current_step = 0
        max_steps = max(1, total_frames // 30)  # Evitar dividir por 0, usar al menos 1 paso

        # Actualizar al 20% al terminar la inicialización
        self.update_state(state='PROGRESS', meta={'percent': 20})

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % 30 == 0:  # Procesar cada 30 cuadros (aproximadamente 1 segundo a 30 fps)
                try:
                    result = DeepFace.analyze(frame, actions=['emotion'])
                    if isinstance(result, list):
                        for face in result:
                            if 'emotion' in face:
                                for emotion, score in face['emotion'].items():
                                    aggregated_emotions[emotion] += score
                                valid_frame_count += 1
                                # Verificar si este frame tiene la emoción dominante
                                current_dominant_emotion = max(face['emotion'], key=face['emotion'].get)
                                if dominant_emotion is None or face['emotion'][current_dominant_emotion] > face['emotion'][dominant_emotion]:
                                    dominant_emotion = current_dominant_emotion
                                    dominant_frame = frame
                    else:
                        # aggregated_emotions['error'] = 'Unexpected result structure'
                        print("=> Estructura de resultado inesperada")
                except Exception as e:
                    # aggregated_emotions['error'] = str(e)
                    print(f"Error durante el análisis del cuadro: {e}")

                # Actualiza el progreso dentro del ciclo
                current_step += 1
                progress = 20 + (current_step / max_steps) * 70  # Progreso entre 20% y 90%
                progress = min(progress, 90)  # Asegurarse de que no supere el 90%
                self.update_state(state='PROGRESS', meta={'percent': progress})
                print(f"=> Paso: {current_step} analizando video => Porcentaje: {progress}%")
            
            frame_count += 1

        # Paso 4: Procesar los resultados después del ciclo `while`
        step = 0
        additional_steps = 3

        end_time = time.time()  # Tiempo de fin
        duration = end_time - start_time  # Duración en segundos

        cap.release()

        # Calcular el promedio de las emociones
        if valid_frame_count > 0:
            for emotion in list(aggregated_emotions.keys()):
                aggregated_emotions[emotion] /= valid_frame_count
            dominant_emotion = max(aggregated_emotions, key=aggregated_emotions.get)
        else:
            aggregated_emotions = {'error': 'No valid frames processed'}
            dominant_emotion = 'unknown'

        # Actualizar el progreso después del ciclo while
        step += 1
        progress = 90 + (step / additional_steps) * 10  # Completar hasta 100%
        self.update_state(state='PROGRESS', meta={'percent': progress})
        print("=> Paso adicional 1: %s" % progress)

        analysis_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        result_summary = {
            'emotions': aggregated_emotions,
            'dominant_emotion': dominant_emotion
        }

        # Actualizar el progreso después del ciclo while
        step += 1
        progress = 90 + (step / additional_steps) * 10  # Completar hasta 100%
        self.update_state(state='PROGRESS', meta={'percent': progress})
        print("=> Paso adicional 2: %s" % progress)
        
        # Paso último: Actualizar emociones en la base de datos
        # video_obj.emotions_detected = result_summary
        
        analysis_result = {
            'emotions': aggregated_emotions,
            'dominant_emotion': dominant_emotion,
            "analysis_time": analysis_time,
            "frame_count": frame_count,
            "duration": duration
        }
        video_obj.emotions_detected = analysis_result
        video_obj.save()

        # Finalmente, actualiza el progreso al 100% solo cuando toda la tarea haya terminado
        self.update_state(state='PROGRESS', meta={'percent': 100})
        print("=> Finalizando análisis: Progreso 100%")

        return {
            "result_summary": result_summary,
            "analysis_time": analysis_time,
            "dominant_emotion": dominant_emotion,
            "frame_count": frame_count,
            "duration": duration
        }

    except ValueError as ve:
        print(f"Error en el análisis de video: {ve}")
        self.update_state(state='FAILURE', meta={'error': f'{type(ve).__name__}: {str(ve)}'})
        raise ve

    except Exception as e:
        print(f"Ocurrió un error inesperado: {e}")
        self.update_state(state='FAILURE', meta={'error': f'{type(e).__name__}: {str(e)}'})
        raise e
