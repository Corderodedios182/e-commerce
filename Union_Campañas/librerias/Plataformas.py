#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar  4 13:15:34 2020

@author: carlos
"""
#Paqueterías
import pandas as pd
import re
import numpy as np

#############################
#Importación de las bases
#   -Limpieza de las bases, formatos, fechas, agrupaciones
#   -Estandarización
#   -Reglas de Fechas
#   -Columnas a ocupar
#   -Ver el nombre de la campaña por rmnt o pi (caso especial)
#
############################

#En caso de querer agregar nuevas validaciones a alguna plataforma corremos por línea
#Y nos traemos los archivos que queremos trabajar
import glob
Mes = '2005_Mayo'

Archivos_csv = glob.glob('C:\\Users\\crf005r\\Documents\\2_Adsocial\\Anual\\ROAS 2020\\ROAS 2020\\' + Mes + '\\**\\*.csv')
Archivos_xlsx = glob.glob('C:\\Users\\crf005r\\Documents\\2_Adsocial\\Anual\\ROAS 2020\\ROAS 2020\\' + Mes + '\\**\\*.xlsx')


def Plataformas_tabla(Archivos_csv, Archivos_xlsx):
    
    ####################
    #Funciones de apoyo#
    ####################
    
    #Fechas 
    def Formato_Fechas(Base, Columna):
        #Es la fecha de inicio del reporte y final del reporte
        if  len((Base.loc[0,Columna]).split(f" - ")) == 2:
            fechas = Base[Columna].astype(str).str.split(" - ",expand = True)
            fechas = pd.DataFrame(fechas)
            fechas.columns = ['inicio_reporte','fin_reporte']
     
            Base['inicio_reporte'] = fechas.iloc[:,0]
            Base['fin_reporte'] = fechas.iloc[:,1]
            
            Base.inicio_reporte = Base.inicio_reporte.apply(lambda x: str(x).replace("['",""))
            Base.fin_reporte = Base.fin_reporte.apply(lambda x: str(x).replace("']",""))
            
            Base.inicio_reporte = pd.to_datetime(Base.inicio_reporte,format = "%Y-%m-%d")
            Base.fin_reporte = pd.to_datetime(Base.fin_reporte,format = "%Y-%m-%d")
            
            return Base
        #En caso de reportes diarios solo saca una fecha el reporte con esto igualamos inicio y fin
        else:
            Base['inicio_reporte'] = Base.loc[:,Columna]
            Base['fin_reporte'] = Base.loc[:,Columna]
            
            Base.inicio_reporte = Base.inicio_reporte.apply(lambda x: str(x).replace("['",""))
            Base.fin_reporte = Base.fin_reporte.apply(lambda x: str(x).replace("']",""))
            
            Base.inicio_reporte = pd.to_datetime(Base.inicio_reporte,format = "%Y-%m-%d")
            Base.fin_reporte = pd.to_datetime(Base.fin_reporte,format = "%Y-%m-%d")
            
            return Base
    
    #mes    
    def mes(x):
        if len(str(x)) == 2:
            y = str(x)
        else:
            y = '0' + str(x)
        return y
    
    #Fecha inicio reporte
    def fechas_inicio(x,y):
        if x <= y:
            return y
        else:
            return x

    #Fecha fin reporte
    def fechas_fin(x,y):
        if x <= y :
            return x
        elif y is pd.NaT:
            return x
        else:
            return y
    
    ###########
    #Facebook #
    ###########    
    Arch_FB = [x for x in Archivos_csv if "FB" in x]
    
    Facebook = []
    
    for csv in Arch_FB:
        
        tmp = pd.read_csv(csv, parse_dates = ['Inicio'], encoding='utf-8')
        tmp['Archivo'] = csv
        Facebook.append(tmp)
    
    Facebook = pd.concat(Facebook).reset_index()

    #Revisiones rápidas
    Facebook.Archivo.value_counts()
    Facebook.keys()
    #Columna de interés
    Facebook = Facebook.loc[:,('Archivo','Nombre de la cuenta','Nombre de la campaña','Mes','Inicio','Finalización','Divisa','Importe gastado (MXN)','Impresiones','Clics en el enlace')]
    Facebook['plataforma'] = 'Facebook'
    Facebook = Facebook.reset_index()
    #Con esta columna extraemos la fecha del reporte
    Facebook.Mes
    
    Facebook.Finalización.apply(lambda x : str(x).replace('Ongoing',''))
    Facebook.Finalización = Facebook.Finalización.apply(lambda x : str(x).replace('Ongoing',''))
    Facebook.Finalización = pd.to_datetime(Facebook.Finalización,format = "%Y-%m-%d",errors = 'ignore')
    
    Facebook = Formato_Fechas(Facebook, 'Mes')

    Facebook.dtypes
    Facebook['Mes'] = Facebook.inicio_reporte.apply(lambda x : mes(x.month))

    #Extracción del nombre para cruzarlo con ventas
    C_Facebook = Facebook.loc[:,'Nombre de la campaña'].str.split("_",10,expand = True).iloc[:,:5] ; cols = ["Año-Mes","Cliente","Marca","Tipo-1","Tipo-2"]
    C_Facebook.columns = cols
    #C_Facebook.loc[:,'Año-Mes'] = Facebook.inicio_reporte.apply(lambda x : str(x.year)[:2] + Facebook['Mes'])
    C_Facebook = C_Facebook[cols].apply(lambda row: '_'.join(row.values.astype(str)), axis=1) ; del cols

    Facebook['llave_plataformas'] = C_Facebook ; del C_Facebook
    Facebook['llave_plataformas'] = Facebook['llave_plataformas'].str.strip()

        #Columnas de interés
    Facebook.keys()
    Facebook = Facebook.loc[:,('Archivo','plataforma','Nombre de la cuenta','Nombre de la campaña','llave_plataformas','Mes','inicio_reporte','fin_reporte',
                               'Inicio','Finalización','Divisa','Importe gastado (MXN)','Impresiones','Clics en el enlace')]

    Facebook.columns = ['archivo','plataforma','cuenta','nombre_campaña','llave_plataformas','mes','inicio_reporte','fin_reporte',
                        'inicio_campaña','fin_campaña','divisa','dinero_gastado','impresiones','clics']

        #Se eliminan las campañas provenientes de estás cuentas puede que no mache con el MP
    Facebook = Facebook.loc[ ~( (Facebook.cuenta.str.contains('Adsocial'))  |  (Facebook.cuenta.str.contains('Dokkoi')) ) ]
    Facebook.llave_plataformas = Facebook.llave_plataformas.str.lower()
    Facebook.llave_plataformas = Facebook.llave_plataformas + str("_fb")

    Facebook['conteo'] = 1

    Facebook.fin_campaña = Facebook.fin_campaña.fillna(Facebook.fin_reporte)
    #Buscamos agrupar correctamente por la llave plataforma ya que esta se repite por que los reportes contienen conjuntos de anuncios y esto ocacionaba duplicados
    
    Facebook['conversiones'] = 0
    Facebook['revenue'] = 0
    Facebook['conversiones_directas'] = 0
    Facebook['conversiones_asistidas'] = 0
    Facebook['revenue_directo'] = 0
    Facebook['revenue_asistido'] = 0
    
    bien_facebook = []
    #Filtro por archivo
    for i in range(0,len(Facebook.archivo.unique())):
        
        Facebook_0 = Facebook[Facebook.archivo == Facebook.archivo.unique()[i]]
        Facebook_0 = Facebook_0.groupby(['plataforma','archivo','cuenta','llave_plataformas','mes','inicio_reporte','fin_reporte','inicio_campaña','fin_campaña','divisa'], as_index = False).agg({
                                                                               'dinero_gastado':'sum',
                                                                               'impresiones':'sum',
                                                                               'clics':'sum',
                                                                               'conversiones':'sum',
                                                                               'revenue':'sum',
                                                                               'conversiones_directas':'sum',
                                                                               'conversiones_asistidas':'sum',
                                                                               'revenue_directo':'sum',
                                                                               'revenue_asistido':'sum',
                                                                               'conteo':'count'})
    
        Facebook_0 = Facebook_0.sort_values('llave_plataformas')
        #Filtro individual por llave_plataforma para agrupar y colocar adecuadamente el inicio y fin de la campaña
        for j in range(0,len(Facebook_0.llave_plataformas.unique())):
            
            a = Facebook_0[Facebook_0.llave_plataformas == Facebook_0.llave_plataformas.unique()[j]]
            
            a.inicio_campaña = a.inicio_campaña.min()
            
            a.fin_campaña = a.fin_campaña.max()
            
            b = a.groupby(['plataforma','archivo','cuenta','llave_plataformas','mes','inicio_reporte','fin_reporte','inicio_campaña','fin_campaña','divisa'], as_index = False).agg({
                                                                                       'dinero_gastado':'sum',
                                                                                       'impresiones':'sum',
                                                                                       'clics':'sum',
                                                                                       'conversiones':'sum',
                                                                                       'revenue':'sum',
                                                                                       'conversiones_directas':'sum',
                                                                                       'conversiones_asistidas':'sum',
                                                                                       'revenue_directo':'sum',
                                                                                       'revenue_asistido':'sum',
                                                                                       'conteo':'sum'})
            bien_facebook.append(b)
    
    bien_facebook = pd.concat(bien_facebook)
        
    bien_facebook['inicio_campaña_reporte'] = [fechas_inicio(x,y) for x, y in zip(bien_facebook.inicio_campaña,bien_facebook.inicio_reporte)] #Este es el bueno      
    bien_facebook['fin_campaña_reporte'] = 0 #"[fechas_fin(x,y) for x, y in zip(bien_facebook.fin_reporte,bien_facebook.fin_campaña)] #Este es el bueno
    bien_facebook['dias_actividad_reporte'] = 0# (bien_facebook['fin_campaña_reporte'] - bien_facebook['inicio_campaña_reporte']).dt.days + 1
    
    bien_facebook.archivo.value_counts()
    bien_facebook.inicio_reporte.value_counts()
    
    #-- Adwords -- #
    Arch_Adwords = [x for x in Archivos_csv if "Adwords" in x]
    
    Adwords = []
    fallas = []

    for csv in Arch_Adwords:
        try:
            tmp = pd.read_csv(csv, delimiter = ',', skiprows = 3, encoding = "latin-1", names = ['Cuenta','Campaña', 'Mes', 'Fecha de inicio', 'Fecha de finalizacion', 'divisa','Costo', 'Impresiones', 'Clics'], header = None)
            tmp['Archivo'] = csv
            #Extreamos las fechas del nombre del reporte
            Fechas = list(tmp.Archivo.unique())
            #####Se extrae la fecha de la columna Archivo, para crear Fecha_inicio_reporte y Fecha_fin_reporte
            tmp['Archivo_fechas'] = tmp['Archivo']
            
            tmp['fecha_reporte'] = [re.findall(r"\d{1}-\d{1}-\d{4}|\d{2}-\d{1}-\d{4}|\d{1}-\d{2}-\d{4}|\d{2}-\d{2}-\d{4}", i) 
                                        for i in list(tmp.Archivo_fechas)]
            
            fechas = [re.findall(r"\d{1}-\d{1}-\d{4}|\d{2}-\d{1}-\d{4}|\d{1}-\d{2}-\d{4}|\d{2}-\d{2}-\d{4}", i) for i in list(tmp.Archivo_fechas)]

            fechas = pd.DataFrame(fechas)
            fechas.columns = ['inicio_reporte','fin_reporte']
        
            tmp = pd.concat([tmp.reset_index(drop = True), pd.DataFrame(fechas)], axis = 1)
        
            Adwords.append(tmp)
        except:
            #En ocasiones por el formato no leía el archivo utf-
            fallas.append(csv)
            print("En ocasiones se guardan como UTF-16 excell ocasionando estas fallas : ",fallas)

    Adwords = pd.concat(Adwords).reset_index(drop = True)

    del Fechas, csv, fallas, fechas, tmp
        #Formato correcto para trabajar con las fechas
    
    #ok
    Adwords['Fecha de inicio'] =  pd.to_datetime(Adwords.loc[:,'Fecha de inicio'],errors='ignore',
                                                 format='%Y-%m-%d')
    #ok
    Adwords['Fecha de finalizacion'] =  pd.to_datetime(Adwords['Fecha de finalizacion'], errors = 'coerce',
                                                       format='%Y-%m-%d')
    #ok
    Adwords['inicio_reporte'] =  pd.to_datetime(Adwords['inicio_reporte'],
                                                format='%d-%m-%Y')
    
    #ok
    Adwords['fin_reporte'] =  pd.to_datetime(Adwords['fin_reporte'],errors='coerce',
                                             format='%d-%m-%Y')
    
    Adwords.keys()
    
    Adwords = Adwords.loc[:,('Archivo','Cuenta','Campaña','Mes','Fecha de inicio','Fecha de finalizacion','inicio_reporte','fin_reporte',
                             'divisa','Costo','Impresiones','Clics')]
    
    Adwords.columns = ('archivo','cuenta','campaña','mes','inicio_campaña','fin_campaña','inicio_reporte','fin_reporte',
                       'divisa','dinero_gastado','impresiones','clics')
    
    Adwords['plataforma'] = 'Adwords'
    
    Adwords['mes'] = Adwords.inicio_reporte.apply(lambda x : mes(x.month))

    #Extracción del nombre para cruzar con ventas
    
    C_Adwords = Adwords.loc[:,'campaña'].str.split("_",10,expand = True).iloc[:,:6] ; cols = ["Año-Mes","Cliente","Marca","Tipo-1","Tipo-2","plataforma"]
    C_Adwords.columns = cols
    C_Adwords.plataforma = C_Adwords.plataforma.fillna('SEM')
    #C_Adwords.loc[:,'Año-Mes'] = Adwords.inicio_reporte.apply(lambda x : str(x.year)[:2] + Adwords['mes'])
    C_Adwords = C_Adwords[cols].apply(lambda row: '_'.join(row.values.astype(str)), axis=1) ; del cols
    
    Adwords['llave_plataformas'] = C_Adwords ; del C_Adwords
    Adwords['llave_plataformas'] = Adwords['llave_plataformas'].str.lower()
    
    #Formato numerico
    Adwords.clics = Adwords.clics.apply(lambda x : str(x).replace(',','')).astype('int')
    Adwords.impresiones = Adwords.impresiones.apply(lambda x: str(x).replace(',','')).astype('int')
    Adwords.dinero_gastado = Adwords.dinero_gastado.apply(lambda x: str(x).replace(',','')).astype('float')
    
    Adwords['plataforma'] = 'Adwords'
    Adwords['conteo'] = 1
    
    Adwords.fin_campaña = Adwords.fin_campaña.fillna(Adwords.fin_reporte)
    #Adwords.cuenta = Adwords.cuenta.fillna('GWEP')
    
    Adwords['conversiones'] = 0
    Adwords['revenue'] = 0
    Adwords['conversiones_directas'] = 0
    Adwords['conversiones_asistidas'] = 0
    Adwords['revenue_directo'] = 0
    Adwords['revenue_asistido'] = 0
    
    bien_adwords = []
        
    #Filtro por archivo
    for i in range(0, len(Adwords.archivo.unique())):
        
        Adwords_0 = Adwords[Adwords.archivo == Adwords.archivo.unique()[i]]
        Adwords_0 = Adwords_0.groupby(['plataforma','archivo','cuenta','llave_plataformas','mes','inicio_reporte','fin_reporte',
                                       'inicio_campaña','fin_campaña','divisa'], as_index = False).agg({
                                                                                                'dinero_gastado':'mean',
                                                                                                'impresiones':'mean',
                                                                                                'clics':'mean',
                                                                                                'conversiones':'sum',
                                                                                                'revenue':'sum',
                                                                                                'conversiones_directas':'sum',
                                                                                                'conversiones_asistidas':'sum',
                                                                                                'revenue_directo':'sum',
                                                                                                'revenue_asistido':'sum',
                                                                                                'conteo':'sum'})
    
        Adwords_0 = Adwords_0.sort_values('llave_plataformas')
        #Filtro individual por llave_plataforma para agrupar y colocar adecuadamente el inicio y fin de la campaña
        for j in range(0,len(Adwords_0.llave_plataformas.unique())):
            
            a = Adwords_0[Adwords_0.llave_plataformas == Adwords_0.llave_plataformas.unique()[j]]
            
            a.inicio_campaña = a.inicio_campaña.min()
            
            a.fin_campaña = a.fin_campaña.max()
            
            b = a.groupby(['plataforma','archivo','cuenta','llave_plataformas','mes','inicio_reporte','fin_reporte','inicio_campaña','fin_campaña','divisa'], as_index = False).agg({
                                                                                       'dinero_gastado':'sum',
                                                                                       'impresiones':'sum',
                                                                                       'clics':'sum',
                                                                                       'conversiones':'sum',
                                                                                       'revenue':'sum',
                                                                                       'conversiones_directas':'sum',
                                                                                       'conversiones_asistidas':'sum',
                                                                                       'revenue_directo':'sum',
                                                                                       'revenue_asistido':'sum',
                                                                                       'conteo':'sum'})
            bien_adwords.append(b)
    
    bien_adwords = pd.concat(bien_adwords)
        
    bien_adwords['inicio_campaña_reporte'] = [ fechas_inicio(x,y) for x, y in zip(bien_adwords.inicio_campaña, bien_adwords.inicio_reporte) ]
    bien_adwords['fin_campaña_reporte'] = [fechas_fin(x,y) for x, y in zip(bien_adwords.fin_reporte,bien_adwords.fin_campaña)] #Este es el bueno
    bien_adwords['dias_actividad_reporte'] = (bien_adwords['fin_campaña_reporte'] - bien_adwords['inicio_campaña_reporte']).dt.days + 1
    
    bien_adwords.archivo.value_counts()
    bien_adwords.inicio_reporte.value_counts()
    
    #-- Adform --#
    Arch_Adform = [x for x in Archivos_xlsx if "Adform" in x]
    
    Adform = []
    
    for xlsx in Arch_Adform:
        tmp = pd.read_excel(xlsx, sheet_name = 'Sheet', skiprows = 2)
        tmp['Archivo'] = xlsx 
        tmp['Archivo_fechas'] = tmp['Archivo']
        Adform.append(tmp)
    
    Adform = pd.concat(Adform)
    
    Adform['fecha_reporte'] = [re.findall(r"\d{1}-\d{1}-\d{4}|\d{2}-\d{1}-\d{4}|\d{1}-\d{2}-\d{4}|\d{2}-\d{2}-\d{4}", i) 
                                        for i in list(Adform.Archivo_fechas)]
    
    fechas = [re.findall(r"\d{1}-\d{1}-\d{4}|\d{2}-\d{1}-\d{4}|\d{1}-\d{2}-\d{4}|\d{2}-\d{2}-\d{4}", i) for i in list(Adform.Archivo_fechas)]
    fechas = pd.DataFrame(fechas)
    fechas.columns = ['inicio_reporte','fin_reporte']
            
    Adform = pd.concat([Adform.reset_index(drop = True), pd.DataFrame(fechas)], axis = 1)
    
    Adform = Adform.iloc[:-1,].loc[:, ('Archivo','Client','Campaign','Month','Campaign Start Date','Campaign End Date','inicio_reporte',
                                       'fin_reporte','Tracked Ads','Clicks','Conversions','Sales (All)')]
    
    Adform['dinero_gastado'] = 0
    Adform['conversiones_directas'] = 0
    Adform['conversiones_asistidas'] = 0
    Adform['revenue_directo'] = 0
    Adform['revenue_asistido'] = 0
    
    Adform.columns = ('archivo','cuenta','campaña','mes','inicio_campaña','fin_campaña','inicio_reporte','fin_reporte',
                      'impresiones','clics','conversiones','revenue','dinero_gastado','conversiones_directas','conversiones_asistidas',
                      'revenue_directo','revenue_asistido')
    
    Adform['plataforma'] = 'Adform'
    Adform['divisa'] = 'MXN'
    
    Adform = Adform.loc[:,('plataforma','archivo','cuenta','campaña','mes','inicio_campaña','fin_campaña','inicio_reporte','fin_reporte','divisa',
                           'dinero_gastado','impresiones','clics','conversiones','revenue','conversiones_directas','conversiones_asistidas',
                           'revenue_directo','revenue_asistido')]
    
        #Fechas 
    Adform.inicio_campaña = pd.to_datetime(Adform.inicio_campaña, format = "%Y-%m-%d")
    Adform.fin_campaña = pd.to_datetime(Adform.fin_campaña,format = "%Y-%m-%d")
    
    Adform.inicio_reporte = pd.to_datetime(Adform.inicio_reporte, format = '%d-%m-%Y')
    Adform.fin_reporte = pd.to_datetime(Adform.fin_reporte,format = '%d-%m-%Y')
    
    Adform['mes'] = Adform.inicio_reporte.apply(lambda x : mes(x.month))
    
    #Extracción del nombre para cruzarlo con ventas
    C_Adform = Adform.loc[:,'campaña'].str.split("_",10,expand = True).iloc[:,:5] ; cols = ["Año-Mes","Cliente","Marca","Tipo-1","Tipo-2"]
    C_Adform.columns = cols
    C_Adform = C_Adform[cols].apply(lambda row: '_'.join(row.values.astype(str)), axis=1)
    
    Adform['llave_plataformas'] = C_Adform ; del C_Adform
    Adform['llave_plataformas'] = Adform['llave_plataformas'].str.strip()
    
    Adform.llave_plataformas = Adform.llave_plataformas.str.lower()
    Adform.llave_plataformas = Adform.llave_plataformas + str("_dsp")
    
    #Formato numerico
    Adform.clics = Adform.clics.apply(lambda x : str(x).replace(',','')).astype('int')
    Adform.impresiones = Adform.impresiones.apply(lambda x: str(x).replace(',','')).astype('int')
    Adform.dinero_gastado = Adform.dinero_gastado.apply(lambda x: str(x).replace(',','')).astype('float')
    Adform.revenue = Adform.revenue.apply(lambda x: str(x).replace(',','')).astype('float')
    
    Adform['conteo'] = 1
    
    Adform.notnull().all()
    Adform.cuenta.value_counts()
    
    bien_adform = []
    
    #Filtro por archivo
    for i in range(0, len(Adform.archivo.unique())):
        
        Adform_0 = Adform[Adform.archivo == Adform.archivo.unique()[i]]
        Adform_0 = Adform_0.groupby(['plataforma','archivo','cuenta','llave_plataformas','mes','inicio_reporte','fin_reporte',
                                       'inicio_campaña','fin_campaña','divisa'], as_index = False).agg({
                                                                                                'dinero_gastado':'mean',
                                                                                                'impresiones':'mean',
                                                                                                'clics':'mean',
                                                                                                'conversiones':'sum',
                                                                                                'revenue':'sum',
                                                                                                'conversiones_directas':'sum',
                                                                                                'conversiones_asistidas':'sum',
                                                                                                'revenue_directo':'sum',
                                                                                                'revenue_asistido':'sum',
                                                                                                'conteo':'sum'})
    
        Adform_0 = Adform_0.sort_values('llave_plataformas')
        #Filtro individual por llave_plataforma para agrupar y colocar adecuadamente el inicio y fin de la campaña
        for j in range(0,len(Adform_0.llave_plataformas.unique())):
            
            a = Adform_0[Adform_0.llave_plataformas == Adform_0.llave_plataformas.unique()[j]]
            
            a.inicio_campaña = a.inicio_campaña.min()
            
            a.fin_campaña = a.fin_campaña.max()
            
            b = a.groupby(['plataforma','archivo','cuenta','llave_plataformas','mes','inicio_reporte','fin_reporte','inicio_campaña','fin_campaña','divisa'], as_index = False).agg({
                                                                                       'dinero_gastado':'sum',
                                                                                       'impresiones':'sum',
                                                                                       'clics':'sum',
                                                                                       'conversiones':'sum',
                                                                                       'revenue':'sum',
                                                                                       'conversiones_directas':'sum',
                                                                                       'conversiones_asistidas':'sum',
                                                                                       'revenue_directo':'sum',
                                                                                       'revenue_asistido':'sum',
                                                                                       'conteo':'sum'})
            bien_adform.append(b)
    
    bien_adform = pd.concat(bien_adform)
    
    bien_adform['inicio_campaña_reporte'] = [fechas_inicio(x,y) for x, y in zip(bien_adform.inicio_campaña, bien_adform.inicio_reporte)] #Este es el bueno      
    bien_adform['fin_campaña_reporte'] = [fechas_fin(x,y) for x, y in zip(bien_adform.fin_reporte, bien_adform.fin_campaña)] #Este es el bueno
    bien_adform['dias_actividad_reporte'] = (bien_adform['fin_campaña_reporte'] - bien_adform['inicio_campaña_reporte']).dt.days + 1

    #Conversiones Asistidas y directas de Adform    
    a = bien_adform[ bien_adform.dias_actividad_reporte <= 0 ]
    b = bien_adform[ bien_adform.dias_actividad_reporte > 0 ]
    
    a = a[a.conversiones > 0]
    a.conversiones_asistidas = a.conversiones
    a.revenue_asistido = a.revenue
    
    b.conversiones_directas = b.conversiones
    b.revenue_directo = b.revenue
    
    bien_adform = pd.concat([a,b])
    
    Adform.archivo.value_counts()
    Adform.inicio_reporte.value_counts()
                                                                                                
    #Unión de las Bases
    # -Unión de todo
    #Facebook.shape[0] + Adwords.shape[0] + Adform.shape[0]
    Plataformas = pd.concat([bien_facebook, bien_adwords, bien_adform])
    
    return Plataformas









