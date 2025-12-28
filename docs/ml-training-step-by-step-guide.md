# Machine Learning Training - Step-by-Step Guide

Complete beginner's guide to ML training for trading pattern recognition.

---

## Overview: What is ML Training?

**Training** = Teaching a computer to recognize patterns by showing it thousands of examples.

**Analogy:** Teaching a child to identify dogs
- Show 1000 dog photos → Child learns "4 legs + fur + tail + barks = dog"
- Show new photo → Child recognizes it's a dog (even if never seen that exact dog)

**In Trading:**
- Show 1000 chart patterns → ML learns "RSI 60-70 + volume spike + positive news = 78% chance price goes up"
- Show new chart → ML predicts outcome

---

## The 5 Phases of ML Training

```
Phase 1: Data Collection
    ↓
Phase 2: Data Preparation (Feature Engineering)
    ↓
Phase 3: Model Training
    ↓
Phase 4: Validation & Testing
    ↓
Phase 5: Deployment & Monitoring
```

---

## Phase 1: Data Collection

### What You Need

**Historical Market Data:**
- **Price data:** Open, High, Low, Close (OHLC) for past 2-5 years
- **Volume data:** Trading volume
- **Indicators:** Pre-calculated RSI, MACD, SMA
- **Labels:** What happened next? (Price went up/down/sideways)

**Example Dataset (Gold Trading):**

```csv
date,open,high,low,close,volume,rsi,sma_20,outcome
2023-01-01,2100,2110,2095,2105,125000,65.2,2098.5,up
2023-01-02,2105,2115,2100,2108,135000,68.1,2100.2,up
2023-01-03,2108,2112,2090,2092,145000,45.3,2101.5,down
...
```

**Labels Explained:**
- `outcome = up` → Price rose >1% in next 4 hours
- `outcome = down` → Price dropped >1% in next 4 hours
- `outcome = sideways` → Price moved <1% in next 4 hours

### How to Get Data

**Option 1: Free APIs (Limited)**
```python
import requests

# Binance API (Crypto)
url = 'https://api.binance.com/api/v3/klines'
params = {
    'symbol': 'BTCUSDT',
    'interval': '1h',
    'limit': 1000
}
response = requests.get(url, params=params)
data = response.json()
```

**Option 2: Paid Data Providers**
- TwelveData ($79/mo) - Your plan uses this
- Alpha Vantage
- Yahoo Finance (free but delayed)

### How Much Data?

**Minimum:**
- 1000 examples (bare minimum, poor accuracy)
- 10,000 examples (decent accuracy ~60-70%)
- 100,000+ examples (good accuracy ~70-80%)

**Why more = better:**
- ML finds patterns by repetition
- More data = model sees more scenarios
- Reduces "overfitting" (explained later)

---

## Phase 2: Data Preparation (Feature Engineering)

### 2.1 Feature Engineering

**Features** = Input variables ML uses to make predictions

**Raw Features (from price data):**
```python
features = {
    'close_price': 2105.50,
    'volume': 125000,
    'rsi': 65.2,
    'sma_20': 2098.30,
    'macd': 12.5
}
```

**Derived Features (calculated):**
```python
# Price momentum (how fast price is changing)
features['momentum'] = (close_price - close_price_5_periods_ago) / close_price_5_periods_ago

# Volatility (how much price swings)
features['volatility'] = std_deviation(last_20_prices)

# Relative position (is price near high or low of range?)
features['position_in_range'] = (close - low_20) / (high_20 - low_20)

# Time features (patterns differ by time of day)
features['hour_of_day'] = 14  # 2 PM
features['day_of_week'] = 3   # Wednesday
```

### 2.2 Data Normalization

**Problem:** Features have different scales
- Price: 2100
- RSI: 65
- Volume: 125000

**Solution:** Scale all features to 0-1 range

```python
from sklearn.preprocessing import MinMaxScaler

# Before normalization
data = [[2105.50, 125000, 65.2]]

# After normalization (0-1 scale)
scaler = MinMaxScaler()
normalized = scaler.fit_transform(data)
# Result: [[0.85, 0.42, 0.65]]
```

**Why normalize?**
- ML treats all numbers equally
- Without normalization, volume (125000) dominates price changes (0.5%)
- After normalization, each feature contributes fairly

### 2.3 Train/Validation/Test Split

**Split data into 3 sets:**

```python
# Total data: 10,000 examples
train_data = data[0:7000]       # 70% for training
validation_data = data[7000:8500]  # 15% for tuning
test_data = data[8500:10000]    # 15% for final testing
```

**Why split?**
- **Train:** Model learns patterns here
- **Validation:** Check if model works on unseen data (tune hyperparameters)
- **Test:** Final accuracy check (NEVER shown to model during training)

**Critical Rule:** NEVER let model see test data during training (cheating!)

---

## Phase 3: Model Training

### 3.1 Choose ML Algorithm

**Popular Algorithms for Trading:**

**1. Random Forest (Recommended for beginners)**
- **How it works:** Creates 100+ decision trees, combines their votes
- **Pros:** Easy to use, handles non-linear patterns, resistant to overfitting
- **Cons:** Slower than simple models
- **Use case:** Pattern classification (buy/sell/hold)

**2. Gradient Boosting (XGBoost)**
- **How it works:** Builds trees sequentially, each correcting previous errors
- **Pros:** Very accurate, handles complex patterns
- **Cons:** Requires tuning, can overfit
- **Use case:** High-accuracy predictions

**3. LSTM (Long Short-Term Memory)**
- **How it works:** Neural network specialized for sequences (price over time)
- **Pros:** Captures time-based patterns (momentum, trends)
- **Cons:** Requires lots of data, expensive to train
- **Use case:** Time series forecasting

### 3.2 Training Process (Random Forest Example)

**Step-by-Step:**

```python
from sklearn.ensemble import RandomForestClassifier
import pandas as pd

# Step 1: Load prepared data
train_df = pd.read_csv('train_data.csv')

# Step 2: Separate features (X) and labels (y)
X_train = train_df[['rsi', 'sma_20', 'volume', 'momentum', 'volatility']]
y_train = train_df['outcome']  # 'up', 'down', 'sideways'

# Step 3: Create model
model = RandomForestClassifier(
    n_estimators=100,     # Number of trees
    max_depth=10,         # How deep each tree goes
    random_state=42       # Reproducibility
)

# Step 4: Train model (THIS IS WHERE "LEARNING" HAPPENS)
model.fit(X_train, y_train)
# During fit():
# - Model tries different tree structures
# - Evaluates which features predict outcome best
# - Adjusts internal weights to minimize errors
# - Repeats until trees converge

print("Training complete!")
```

**What happens during `fit()`?**

1. **Iteration 1:** Model makes random guesses
   - Guess: "If RSI > 50, predict 'up'" → 52% accuracy (barely better than coin flip)

2. **Iteration 100:** Model learns better rules
   - Rule: "If RSI 60-70 AND volume > avg AND momentum positive → 78% predict 'up'"

3. **Final:** Model has learned which feature combinations predict outcomes

### 3.3 Hyperparameter Tuning

**Hyperparameters** = Settings you choose BEFORE training

```python
# Hyperparameters for Random Forest
hyperparameters = {
    'n_estimators': 100,      # More trees = more accurate but slower
    'max_depth': 10,          # Deeper = captures complex patterns but risks overfitting
    'min_samples_split': 20   # Minimum data needed to split a branch
}
```

**How to find best values?**

```python
from sklearn.model_selection import GridSearchCV

# Try different combinations
param_grid = {
    'n_estimators': [50, 100, 200],
    'max_depth': [5, 10, 15],
    'min_samples_split': [10, 20, 50]
}

# Test all 27 combinations (3 × 3 × 3)
grid_search = GridSearchCV(
    RandomForestClassifier(),
    param_grid,
    cv=5  # 5-fold cross-validation
)

grid_search.fit(X_train, y_train)
best_model = grid_search.best_estimator_

print(f"Best params: {grid_search.best_params_}")
# Output: {'n_estimators': 100, 'max_depth': 10, 'min_samples_split': 20}
```

---

## Phase 4: Validation & Testing

### 4.1 Evaluate on Validation Set

```python
from sklearn.metrics import accuracy_score, classification_report

# Predict on validation data (model hasn't seen this)
val_df = pd.read_csv('validation_data.csv')
X_val = val_df[['rsi', 'sma_20', 'volume', 'momentum', 'volatility']]
y_val = val_df['outcome']

predictions = model.predict(X_val)

# Calculate accuracy
accuracy = accuracy_score(y_val, predictions)
print(f"Validation Accuracy: {accuracy * 100:.1f}%")
# Output: Validation Accuracy: 72.3%

# Detailed metrics
print(classification_report(y_val, predictions))
```

**Output Example:**
```
              precision    recall  f1-score   support
        down       0.68      0.75      0.71       450
    sideways       0.65      0.58      0.61       600
          up       0.80      0.78      0.79       450

    accuracy                           0.72      1500
```

**What these mean:**
- **Precision:** When model predicts "up", how often is it right? (80%)
- **Recall:** Of all actual "up" cases, how many did model catch? (78%)
- **F1-score:** Harmonic mean of precision & recall (79%)

### 4.2 Overfitting Check

**Overfitting** = Model memorizes training data but fails on new data

**Symptoms:**
```
Training Accuracy: 98%   ← Too good!
Validation Accuracy: 62% ← Poor on new data
```

**Analogy:** Student memorizes test answers without understanding
- Ace practice test (98%)
- Fail real exam (62%)

**How to detect:**
```python
train_acc = model.score(X_train, y_train)
val_acc = model.score(X_val, y_val)

print(f"Train: {train_acc:.2%}, Val: {val_acc:.2%}")

if train_acc - val_acc > 0.15:  # >15% gap
    print("⚠️ Overfitting detected!")
    # Solutions:
    # 1. Get more training data
    # 2. Reduce model complexity (lower max_depth)
    # 3. Add regularization
```

### 4.3 Feature Importance

**Which features matter most?**

```python
import matplotlib.pyplot as plt

# Get feature importance scores
importances = model.feature_importances_
features = ['rsi', 'sma_20', 'volume', 'momentum', 'volatility']

# Sort by importance
importance_df = pd.DataFrame({
    'feature': features,
    'importance': importances
}).sort_values('importance', ascending=False)

print(importance_df)
```

**Output:**
```
     feature  importance
0        rsi       0.35   ← RSI most important (35%)
3   momentum       0.28
4 volatility       0.18
2     volume       0.12
1     sma_20       0.07
```

**Insight:** Focus on RSI and momentum - they drive 63% of predictions

### 4.4 Final Test (NEVER DONE BEFORE THIS)

```python
# Test on completely unseen data
test_df = pd.read_csv('test_data.csv')
X_test = test_df[['rsi', 'sma_20', 'volume', 'momentum', 'volatility']]
y_test = test_df['outcome']

test_accuracy = model.score(X_test, y_test)
print(f"Final Test Accuracy: {test_accuracy * 100:.1f}%")
# Output: Final Test Accuracy: 71.8%

# If test_accuracy ≈ val_accuracy → Model generalizes well ✅
# If test_accuracy << val_accuracy → Overfitting ❌
```

---

## Phase 5: Deployment & Monitoring

### 5.1 Save Trained Model

```python
import joblib

# Save model to file
joblib.dump(model, 'trading_model.pkl')
joblib.dump(scaler, 'scaler.pkl')  # Save normalization parameters too!

# Load later in production
loaded_model = joblib.load('trading_model.pkl')
loaded_scaler = joblib.load('scaler.pkl')
```

### 5.2 Production Inference

```python
# Real-time prediction in Capital Companion backend
def predict_market_move(current_data: dict) -> dict:
    """
    Predict if Gold will go up/down/sideways

    Args:
        current_data: {
            'rsi': 65.2,
            'sma_20': 2098.5,
            'volume': 125000,
            'momentum': 0.015,
            'volatility': 0.025
        }

    Returns:
        {
            'prediction': 'up',
            'confidence': 0.78,
            'probabilities': {'up': 0.78, 'down': 0.12, 'sideways': 0.10}
        }
    """
    # Step 1: Normalize features (using same scaler from training!)
    features = [
        current_data['rsi'],
        current_data['sma_20'],
        current_data['volume'],
        current_data['momentum'],
        current_data['volatility']
    ]
    normalized = loaded_scaler.transform([features])

    # Step 2: Get prediction
    prediction = loaded_model.predict(normalized)[0]

    # Step 3: Get probabilities (confidence scores)
    probabilities = loaded_model.predict_proba(normalized)[0]
    proba_dict = dict(zip(['down', 'sideways', 'up'], probabilities))

    # Step 4: Confidence = probability of predicted class
    confidence = max(probabilities)

    return {
        'prediction': prediction,
        'confidence': round(confidence, 2),
        'probabilities': {k: round(v, 2) for k, v in proba_dict.items()}
    }

# Example usage
result = predict_market_move({
    'rsi': 65.2,
    'sma_20': 2098.5,
    'volume': 125000,
    'momentum': 0.015,
    'volatility': 0.025
})

print(result)
# Output:
# {
#     'prediction': 'up',
#     'confidence': 0.78,
#     'probabilities': {'up': 0.78, 'down': 0.12, 'sideways': 0.10}
# }
```

### 5.3 Monitor Model Performance

**Production Monitoring:**

```python
# Track predictions vs actual outcomes
class ModelMonitor:
    def __init__(self):
        self.predictions = []
        self.actuals = []

    def log_prediction(self, prediction, actual_outcome):
        """Call this after each prediction + 4 hours later when outcome known"""
        self.predictions.append(prediction)
        self.actuals.append(actual_outcome)

    def calculate_accuracy(self):
        """Weekly accuracy check"""
        from sklearn.metrics import accuracy_score
        return accuracy_score(self.actuals, self.predictions)

    def alert_degradation(self):
        """Alert if accuracy drops below threshold"""
        accuracy = self.calculate_accuracy()

        if accuracy < 0.65:  # Below 65%
            print(f"⚠️ Model degradation! Accuracy: {accuracy:.1%}")
            print("Action: Retrain model with recent data")
            # Send alert to team
            # Trigger retraining pipeline
```

**Why monitoring matters:**
- Markets change over time (2023 patterns ≠ 2024 patterns)
- Model accuracy degrades ("model drift")
- Need retraining every 3-6 months

### 5.4 Retraining Strategy

```python
# Automated retraining (every 3 months)
def retrain_model():
    """Retrain with latest data"""

    # 1. Fetch new data (last 3 months)
    new_data = fetch_recent_market_data(days=90)

    # 2. Combine with existing training data
    updated_train = pd.concat([old_train_data, new_data])

    # 3. Keep only recent 2 years (rolling window)
    updated_train = updated_train.tail(17520)  # 2 years of hourly data

    # 4. Retrain model
    X_new = updated_train[features]
    y_new = updated_train['outcome']
    model.fit(X_new, y_new)

    # 5. Validate
    val_acc = model.score(X_val, y_val)
    if val_acc < previous_accuracy - 0.05:  # Accuracy dropped >5%
        print("⚠️ New model worse than old - rolling back")
        return  # Don't deploy

    # 6. Deploy new model
    joblib.dump(model, 'trading_model.pkl')
    print(f"✅ Model retrained. New accuracy: {val_acc:.1%}")
```

---

## Complete Training Pipeline Example

```python
# Full pipeline from data to deployment
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# ===== STEP 1: LOAD DATA =====
print("Loading data...")
df = pd.read_csv('gold_historical_5years.csv')
print(f"Loaded {len(df)} rows")

# ===== STEP 2: FEATURE ENGINEERING =====
print("Creating features...")
df['momentum'] = (df['close'] - df['close'].shift(5)) / df['close'].shift(5)
df['volatility'] = df['close'].rolling(20).std()
df['position_in_range'] = (df['close'] - df['low'].rolling(20).min()) / \
                          (df['high'].rolling(20).max() - df['low'].rolling(20).min())

# Drop NaN rows
df = df.dropna()

# ===== STEP 3: PREPARE X AND Y =====
features = ['rsi', 'sma_20', 'volume', 'momentum', 'volatility', 'position_in_range']
X = df[features]
y = df['outcome']

# ===== STEP 4: SPLIT DATA =====
X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)

print(f"Train: {len(X_train)}, Val: {len(X_val)}, Test: {len(X_test)}")

# ===== STEP 5: NORMALIZE =====
scaler = MinMaxScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)
X_test_scaled = scaler.transform(X_test)

# ===== STEP 6: TRAIN MODEL =====
print("Training model...")
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train_scaled, y_train)

# ===== STEP 7: VALIDATE =====
train_acc = model.score(X_train_scaled, y_train)
val_acc = model.score(X_val_scaled, y_val)

print(f"Train Accuracy: {train_acc:.1%}")
print(f"Val Accuracy: {val_acc:.1%}")

if train_acc - val_acc > 0.15:
    print("⚠️ Overfitting detected!")

# ===== STEP 8: FINAL TEST =====
test_acc = model.score(X_test_scaled, y_test)
print(f"Test Accuracy: {test_acc:.1%}")

y_pred = model.predict(X_test_scaled)
print(classification_report(y_test, y_pred))

# ===== STEP 9: FEATURE IMPORTANCE =====
importance_df = pd.DataFrame({
    'feature': features,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
print("\nFeature Importance:")
print(importance_df)

# ===== STEP 10: SAVE MODEL =====
joblib.dump(model, 'models/gold_trading_model.pkl')
joblib.dump(scaler, 'models/gold_scaler.pkl')
print("\n✅ Model saved to models/")
```

---

## Common Pitfalls & Solutions

### 1. **Data Leakage**

**Problem:** Future data leaks into training
```python
# ❌ BAD: Using future price to predict current
df['label'] = (df['close'].shift(-4) > df['close']).astype(int)  # Shift -4 = looking ahead!
```

**Solution:**
```python
# ✅ GOOD: Use only past data
df['label'] = (df['close'].shift(4) > df['close'].shift(0)).astype(int)  # Shift 4 = looking back
```

### 2. **Class Imbalance**

**Problem:** 70% "sideways", 20% "up", 10% "down" → Model always predicts "sideways"

**Solution:** Balance classes
```python
from imblearn.over_sampling import SMOTE

# Oversample minority classes
smote = SMOTE(random_state=42)
X_balanced, y_balanced = smote.fit_resample(X_train, y_train)
```

### 3. **Ignoring Market Regime Changes**

**Problem:** Model trained on bull market fails in bear market

**Solution:** Add regime features
```python
# Detect market regime
df['regime'] = 'bull' if df['sma_200'].iloc[-1] > df['sma_200'].iloc[-50] else 'bear'
# Train separate models per regime
```

---

## Cost Estimate (ML Training)

**One-time Training:**
- Local GPU (RTX 3080): $0 (your hardware)
- Cloud GPU (AWS p3.2xlarge): $3.06/hour × 2 hours = $6
- Google Colab Pro: $9.99/month (includes GPU)

**Inference (Production):**
- CPU inference: $0.001 per prediction (very cheap)
- Cloud ML API: $0.01-0.10 per prediction

**Your Capital Companion Scale:**
- 1000 users × 10 predictions/day = 10k predictions/day
- Cost: $10-100/day ($300-3000/month)

**Why Rule-Based is recommended:** $0 inference cost!

---

## Next Steps for Capital Companion

**Phase 1 (Recommended):** Rule-Based Only
- Zero ML training needed
- Use RSI code examples from previous doc
- Cost: $0

**Phase 2 (Future):** Hybrid Approach
- Use Rule-Based for alerts
- Add ML for confidence scoring: "This RSI signal has 78% historical accuracy"
- Train model on user feedback ("Did this alert help? Yes/No")

**Phase 3 (Advanced):** Full ML
- Train LSTM on 5 years Gold/Crypto data
- Deploy model API
- Monitor & retrain quarterly

---

## Unresolved Questions

1. Should Atlas use ML predictions or rule-based signals for beta launch?
2. What accuracy threshold is "trustworthy" for users? (70%? 80%?)
3. How to explain ML predictions to non-technical users?
4. Should model be user-specific (personalized) or global (one model for all)?
