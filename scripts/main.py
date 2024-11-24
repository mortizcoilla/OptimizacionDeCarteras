# Carga de Librerias

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from pypfopt import EfficientFrontier, objective_functions
from pypfopt import risk_models
from pypfopt import expected_returns
import cvxpy as cp
from scipy.optimize import minimize

# Lista de tickers de las empresas IPSA

tickers =  ["SQM","BCH","BSANTANDER.SN","CENCOSUD.SN","COPEC.SN","ENELAM.SN","BCI.SN","CMPC.SN","FALABELLA.SN","ENELCHILE.SN",
            "COLBUN.SN","PARAUCO.SN","VAPORES.SN","AGUAS-A.SN","ANDINA-B.SN","CCU.SN","QUINENCO.SN","CENCOSHOPP.SN","LTM.SN",
            "CONCHATORO.SN","ENTEL.SN","MALLPLAZA.SN","CAP.SN","ECL.SN","ITAUCL.SN","ORO-BLANCO.SN","IAM.SN","SMU.SN","RIPLEY.SN",
            "SONDA.SN"]

# Definimos la fecha de inicio y fin para los últimos 5 años
end_date = pd.Timestamp.today()
start_date = end_date - pd.DateOffset(years=5)

# Descargamos los datos
data = yf.download(tickers, start=start_date, end=end_date, interval="1wk")

# Seleccionamos solo el 'Adj Close' que es el precio de cierre ajustado
prices = data['Adj Close']
