## regresion logistica_modelo 2.ipynb
Se realizaron graficos descriptivos, un modelo provisional de OLS logit para la seleccion de variables con todas las variables estandarizadas y separadas en tain y test para no hacer un modelo muy optimista y un segundo modelo logistico al que se le introcieron las variables mas significativas del modelo anterior  previamente estandarizadas y separadas en train y test. Al modelo se le aplico regularizacion para que generalizara mejor y no hubiera overfitting, los hiperparametros de la regularizacion se calcularon mediante un random search y cross validation. Por ultimo se decidio el mejor modelo basado en la metrica que mas interesaba que era ROC-AUC ya que en el resto de metricas tampoco habia mucha diferencia entre los diferentes modelos. Para terminar, se calcularon las probabilidades de impago y se añadieron al un dataframe nuevo exportandolo para su futuro uso en el modelo de regreion polinomica. 

## modelo de regresion polinomica final.ipynb
Se realizaron graficos descriptivos, un modelo provisional OLS para seleccion de variables con todas las variables estandarizadas y separadas en tain y test para no hacer un modelo muy optimista, un segundo modelo polinomico al que se le intocudieron las variables  mas significativas del modelo anterior previamente estandarizadas y separadas en train y test. Con los resultados del segundo modelo se hicieron curvas de aprendizaje junto con cross validation de 5 particiones para estudiar la evolución del error. En base a las metricas de error, numero de variables y curvas de aprendizaje de los ultimos modelos polinomicos se seleciono el mejor modelo predictivo de la "Prima". Se intento regularizar el modelo ganador de grado 3 junto a randomsearch y cross validaton para encontrar los mejores hipermaratetros de dichos modelos con el objetivo de reducir el numero de variables, pero despues de analizar los resultados se decidio no tener en cuenta el modelo regularizado ya que empeoraba las metricas de error y no eliminaba vaiables suficienetes, por lo que se descarto y se quedo como modelo final el modelo polinomico de grado 3 sin regularizar.

## tratamiento de datos.ipynb
Se realizo un tratamiento de datos y filtrado, el filtrado se hizo para solo tener las filas de la categoria negocio, y en el tratemiento se detectaron y eliminaron datos duplicados y nulos. Por ultimo se hicieron dummys dos variables para su posterior uso.

## analisis_exploratorio_na.ipynb
Se realizaron graficos para facilitar la comprension de los datos y asi poder realizar tratamientos o analiasis mejores.

## docker 5 alumnos
Esta carpeta consta de todo lo relacionado a API, dentro de ella se encuntra un segundo readme detallado sobre el contenido de esa carpeta.

## power bi
Esta carpeta contiene el archivo del dashboard con graficos 

## sistema_aleman
Se crea una primera prueba de las cuotas de cada uno de los préstamos con el sistema alemán 

## sistema_frances
Se crea una primera prueba de las cuotas de cada uno de los préstamos con el sistema frances 

## sistema_finanzas_final
He analizado los préstamos de negocios, comparado los sistemas de amortización francés y alemán y elegido uno para cada préstamo según la cuota y los intereses. Después, he calculado el valor de las cuotas pendientes a mitad del plazo y he usado el VAN y la TIR para valorar la rentabilidad de cada préstamo desde el punto de vista del prestamista.
