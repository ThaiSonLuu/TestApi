# 🏥 Health Prediction ML Model

Mô hình Machine Learning dự báo tình trạng sức khỏe theo mùa dựa trên triệu chứng và điều kiện môi trường.

## 📋 Tổng quan

Hệ thống bao gồm:

- **train_model.py**: Train mô hình ML từ dữ liệu
- **predict.py**: Sử dụng mô hình để dự đoán bệnh
- **sample_patient.json**: Dữ liệu bệnh nhân mẫu

## 🚀 Cài đặt

### 1. Tạo môi trường ảo

```bash
python -m venv venv
source venv/bin/activate
```

### 2. Cài đặt dependencies

#### Sử dụng pip

```bash
pip install -r requirements.txt
```

## 🤖 Train Mô hình

### Train với dữ liệu mẫu (tự động tạo)

```bash
python train_model.py
```

Kết quả train sẽ hiển thị:

- Accuracy score
- Cross-validation score
- Feature importance
- Classification report
- Model được lưu vào `health_prediction_model.pkl`

### Train với dữ liệu custom

```bash
# Tạo file CSV với format như health_data_sample.csv
python train_model.py --data your_data.csv
```

### Kết quả mong đợi

```
🏥 Health Prediction Model Training
==================================================
📊 Creating sample data...
✅ Created 1000 training samples
Disease distribution:
Healthy              400
Seasonal Flu         250
Common Cold          150
Allergic Rhinitis    100
Heat Exhaustion       50
Gastroenteritis       50

🤖 Starting model training...
🎯 Training Random Forest model...

📈 Training Results:
Accuracy: 0.8950
CV Score: 0.8875 (+/- 0.0234)

🔍 Top 5 Important Features:
  fever: 0.1834
  fatigue: 0.1623
  body_aches: 0.1456
  temperature: 0.1234
  weather_temp: 0.0987

✅ Training completed successfully!
💾 Model saved to health_prediction_model.pkl
```

## 🔮 Dự đoán

### 1. Dự đoán với dữ liệu mẫu

```bash
python predict.py --sample
```

### 2. Dự đoán tương tác (nhập liệu từ bàn phím)

```bash
python predict.py --interactive
```

Ví dụ nhập liệu:

```
🩺 Nhập thông tin bệnh nhân:
------------------------------
Tuổi: 30
Giới tính (nam/nữ): nữ

Triệu chứng (y/n):
Sốt: y
Ho: y
Đau đầu: n
Đau họng: y
Sổ mũi: n
Mệt mỏi: y
Đau nhức cơ thể: y

Nhiệt độ cơ thể (°C, enter để bỏ qua): 38.5

Thông tin thời tiết:
Nhiệt độ thời tiết (°C): 20
Độ ẩm (%): 70
Chất lượng không khí (1-5): 3

Đi du lịch gần đây (y/n): n
Tiếp xúc với người bệnh (y/n): y
Tháng hiện tại (1-12): 4
```

### 3. Dự đoán từ file JSON

```bash
python predict.py --json sample_patient.json
```

### 4. Dự đoán với model custom

```bash
python predict.py --model your_model.pkl --sample
```

## 📊 Kết quả Dự đoán

```
🏥 Health Prediction Service
========================================
✅ Model loaded successfully!
📂 Model loaded from health_prediction_model.pkl
Trained at: 2024-01-15T10:30:45.123456

🔮 Making prediction...

📊 Prediction Results:
Predicted Disease: Seasonal Flu
Confidence: 0.8750 (87.5%)

🏆 Top 3 Predictions:
  1. Seasonal Flu: 0.8750 (87.5%)
  2. Common Cold: 0.1050 (10.5%)
  3. Healthy: 0.0200 (2.0%)

⏰ Prediction Time: 2024-01-15T14:22:33.456789
💾 Result saved to prediction_result_20240115_142233.json
```

## 📝 Định dạng dữ liệu

### Input Features (17 features)

```json
{
  "age": 30, // Tuổi (5-80)
  "gender": 1, // Giới tính (0=nữ, 1=nam)
  "temperature": 38.2, // Nhiệt độ cơ thể (°C)
  "fever": 1, // Sốt (0=không, 1=có)
  "cough": 1, // Ho
  "headache": 0, // Đau đầu
  "sore_throat": 1, // Đau họng
  "runny_nose": 0, // Sổ mũi
  "fatigue": 1, // Mệt mỏi
  "body_aches": 1, // Đau nhức cơ thể
  "weather_temp": 22, // Nhiệt độ thời tiết (°C)
  "humidity": 70, // Độ ẩm (%)
  "air_quality": 3, // Chất lượng không khí (1-5)
  "season": 1, // Mùa (0=đông, 1=xuân, 2=hè, 3=thu)
  "month": 4, // Tháng (1-12)
  "recent_travel": 0, // Du lịch gần đây (0=không, 1=có)
  "contact_sick": 1 // Tiếp xúc người bệnh (0=không, 1=có)
}
```

### Output Diseases (6 loại bệnh)

- **Healthy**: Khỏe mạnh
- **Common Cold**: Cảm lạnh thông thường
- **Seasonal Flu**: Cúm mùa
- **Allergic Rhinitis**: Viêm mũi dị ứng
- **Heat Exhaustion**: Kiệt sức do nắng nóng
- **Gastroenteritis**: Viêm dạ dày ruột

## 🔧 Tùy chỉnh Model

### Thay đổi thuật toán

Sửa trong `train_model.py`:

```python
# Thay RandomForestClassifier bằng thuật toán khác
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier

self.model = SVC(probability=True, random_state=42)
# hoặc
self.model = MLPClassifier(hidden_layer_sizes=(100, 50), random_state=42)
```

### Thêm features mới

Thêm vào `create_sample_data()`:

```python
data['new_feature'] = np.random.choice([0, 1], n_samples)
```

### Thêm bệnh mới

Sửa logic trong `create_sample_data()`:

```python
elif (your_conditions):
    diseases.append('New Disease')
```

## 📈 Đánh giá Model

### Xem chi tiết performance

```bash
python -c "
from train_model import HealthPredictionTrainer
trainer = HealthPredictionTrainer()
trainer.load_model()
print('Model info:', trainer.model_data)
"
```

### Batch prediction nhiều bệnh nhân

```python
from predict import HealthPredictor

predictor = HealthPredictor()
patients = [patient1_data, patient2_data, patient3_data]
results = predictor.predict_batch(patients)
print(results)
```

## ⚠️ Lưu ý

1. **Dữ liệu mẫu**: Chỉ để demo, không dùng cho chẩn đoán thực tế
2. **Model accuracy**: ~87-90% trên dữ liệu mẫu
3. **Medical disclaimer**: Không thay thế tư vấn y tế chuyên nghiệp
4. **Input validation**: Luôn kiểm tra dữ liệu đầu vào

## 🐛 Troubleshooting

### Lỗi scikit-learn trên macOS

```bash
# Cài đặt qua conda thay vì pip
conda install scikit-learn

# Hoặc fix OpenMP
brew install libomp
export LDFLAGS="-L/opt/homebrew/lib -lomp"
pip install scikit-learn
```

### Lỗi "Model not found"

```bash
# Train model trước khi predict
python train_model.py
```

### Lỗi "Missing features"

Đảm bảo input có đủ 17 features theo format sample_patient.json

## 📞 Hỗ trợ

- File issues nếu gặp lỗi
- Xem log chi tiết trong console output
- Check requirements.txt compatibility

---

**⚕️ Disclaimer**: Đây là mô hình demo cho mục đích học tập. Không sử dụng để chẩn đoán y tế thực tế.
