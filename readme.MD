# 🏥 Health Prediction ML Model

Mô hình Machine Learning dự báo tình trạng sức khỏe theo mùa dựa trên triệu chứng và điều kiện môi trường.

## 🚀 Cài đặt

### 1. Tạo môi trường ảo

```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Cài đặt dependencies

#### Sử dụng pip

```bash
pip install -r requirements.txt
```

### 3. Tạo database

```bash
cd docker/
docker compose up -d
```

### 4. Chạy server

```bash
python3 -B -m src.app
```
