import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib
import os

def entrenar_modelo_prediccion(ordenes_entregadas):
    """
    Entrena un modelo de Machine Learning clásico basado en Random Forest 
    para predecir los días estimados de reparación.
    """
    if len(ordenes_entregadas) < 3:
        return None

    X = [] # Características
    y = [] # Días

    for o in ordenes_entregadas:

        if o.fecha_recepcion and o.fecha_entrega:
            delta = o.fecha_entrega - o.fecha_recepcion
            dias_reales = max(1, delta.days) 


            num_repuestos = o.repuestos_usados.count() if hasattr(o, 'repuestos_usados') else 0
            tecnico_id = o.tecnico.id if o.tecnico else 0
            longitud_falla = len(o.descripcion_problema or '')

            X.append([num_repuestos, tecnico_id, longitud_falla])
            y.append(dias_reales)

    if not X:
        return None


    modelo = RandomForestRegressor(n_estimators=50, random_state=42)
    modelo.fit(np.array(X), np.array(y))


    joblib.dump(modelo, 'modelo_dias_reparacion.pkl')
    return modelo

def predecir_dias_orden(num_repuestos, tecnico_id, descripcion_falla):
    """
    Predice los días que tardará una nueva orden de trabajo.
    """
    modelo_path = 'modelo_dias_reparacion.pkl'
    if not os.path.exists(modelo_path):
        return 3 

    modelo = joblib.load(modelo_path)
    longitud_falla = len(descripcion_falla or '')
    
 
    prediccion = modelo.predict([[num_repuestos, tecnico_id or 0, longitud_falla]])
    return max(1, round(prediccion[0]))
