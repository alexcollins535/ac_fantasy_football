import pandas as pd
import numpy as np
import fantasy_football.ffl_create_features as fcf
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
#from sklearn.linear_model import LinearRegression, Lasso, Ridge
from sklearn.metrics import root_mean_squared_error
from sklearn.ensemble import GradientBoostingRegressor


# Unable to create a linear or ensemble model to predict FPTS or FPTS_CLASS with a positive R squared value. 

SEED = 10142024

qb_data_set = fcf.import_model_data('QB')

X = qb_data_set.drop(labels=['PLAYER', 'TEAM', 'OPPONENT', 'POS', 'FPTS', 'WEEK', 'FPTS_CLASS'], axis=1)
features = X.columns
y = qb_data_set['FPTS_CLASS']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=SEED)

# Preprocessing: standardize the data with StandardScaler
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Trying linear regression, ridge, and lasso models first
#linreg = LinearRegression()
#ridge = Ridge(alpha=0.1)
#lasso = Lasso(alpha=0.1)
#('LinReg', linreg), ('Ridge', ridge), ('Lasso', lasso)
# Result: all three models returned R2 values under 0 (around -0.1) and RMSE values around 10.2.

# Trying Gradient Boosting Regressor with hyperparameter tuning
gbr = GradientBoostingRegressor(n_estimators=400, max_depth=4, loss='absolute_error', min_samples_leaf=4, random_state=SEED)
#param_grid = {'max_depth': [3, 4, 5], 
#            'n_estimators': [375, 400, 425], 
#            'min_samples_leaf': [4], 
#            'loss': ['absolute_error']}
#cv = GridSearchCV(estimator=gbr, param_grid=param_grid)

coefficients = {}
scores = []

model = gbr
name = 'GBR'
print('Fitting model...')
model.fit(X_train_scaled, y_train)
#print(model.best_params_)
#print(model.best_score_) # note this is r_squared

y_pred = model.predict(X_test_scaled)
r_squared = np.round(model.score(X_test_scaled, y_test), 3)
rmse = np.round(root_mean_squared_error(y_test, y_pred), 3)
scores = (r_squared, rmse)
coefficients[name] = list(model.feature_importances_)
feature_table = pd.DataFrame(coefficients, index=features)
print(scores)
print(feature_table)
