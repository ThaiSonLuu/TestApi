-- Health Predictor System Database v2
-- Khởi tạo database cho hệ thống dự đoán sức khỏe với ML

-- Tạo bảng người dùng hệ thống
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50),
    last_name VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(10), -- male, female, other
    phone VARCHAR(20),
    address TEXT,
    
    -- Thông tin riêng cho người bệnh
    current_latitude DOUBLE PRECISION, -- Vị trí hiện tại - chỉ cho patient
    current_longitude DOUBLE PRECISION, -- Vị trí hiện tại - chỉ cho patient
    current_diseases TEXT, -- Bệnh đang mắc - JSON array of disease IDs
    
    -- Thông tin chung
    role VARCHAR(20) NOT NULL CHECK (role IN ('doctor', 'patient', 'admin')),
    is_active BOOLEAN DEFAULT TRUE
);

-- Tạo index cho bảng users
CREATE INDEX IF NOT EXISTS idx_users_name ON users(first_name, last_name);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_user_location ON users(current_latitude, current_longitude);

-- Tạo bảng các triệu chứng
CREATE TABLE IF NOT EXISTS symptoms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE, -- Mã triệu chứng
    description TEXT
);

-- Tạo index cho bảng symptoms
CREATE INDEX IF NOT EXISTS idx_symptoms_code ON symptoms(code);

-- Tạo bảng các loại bệnh
CREATE TABLE IF NOT EXISTS diseases (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    code VARCHAR(20) UNIQUE, -- ICD-10 hoặc mã tự định nghĩa
    description TEXT,
    
    -- Thông tin về khả năng lây truyền
    is_contagious BOOLEAN DEFAULT FALSE NOT NULL -- Có lây truyền không
);

-- Tạo index cho bảng diseases
CREATE INDEX IF NOT EXISTS idx_diseases_name ON diseases(name);
CREATE INDEX IF NOT EXISTS idx_diseases_code ON diseases(code);
CREATE INDEX IF NOT EXISTS idx_diseases_contagious ON diseases(is_contagious);

-- Tạo bảng lịch sử bệnh án
CREATE TABLE IF NOT EXISTS medical_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, -- Người bệnh
    doctor_id INTEGER REFERENCES users(id) ON DELETE SET NULL, -- Bác sĩ chẩn đoán (null nếu là hệ thống)
    record_type VARCHAR(20) NOT NULL CHECK (record_type IN ('doctor_diagnosis', 'system_prediction')),
    confidence_score DOUBLE PRECISION, -- Độ tin cậy (chỉ cho system_prediction)
    status VARCHAR(50), -- new, completed
    is_accurate BOOLEAN, -- Có chính xác hay không (đánh giá sau khi có kết quả thực tế)
    weather_temp DOUBLE PRECISION, -- Nhiệt độ thời tiết (°C)
    humidity INTEGER, -- Độ ẩm (%)
    air_quality_index INTEGER, -- Chỉ số chất lượng không khí
    season VARCHAR(20) -- spring, summer, autumn, winter
);

-- Tạo index cho bảng medical_records
CREATE INDEX IF NOT EXISTS idx_medical_records_user ON medical_records(user_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_doctor ON medical_records(doctor_id);
CREATE INDEX IF NOT EXISTS idx_medical_records_type ON medical_records(record_type);

-- Tạo bảng triệu chứng trong từng bệnh án (many-to-many)
CREATE TABLE IF NOT EXISTS record_symptoms (
    record_id INTEGER NOT NULL REFERENCES medical_records(id) ON DELETE CASCADE,
    symptom_id INTEGER NOT NULL REFERENCES symptoms(id) ON DELETE CASCADE,
    
    PRIMARY KEY (record_id, symptom_id)
);

-- Tạo index cho bảng record_symptoms
CREATE INDEX IF NOT EXISTS idx_record_symptoms_symptom ON record_symptoms(symptom_id);

-- Tạo bảng bệnh được chẩn đoán trong từng bệnh án (many-to-many)
CREATE TABLE IF NOT EXISTS record_diseases (
    record_id INTEGER NOT NULL REFERENCES medical_records(id) ON DELETE CASCADE,
    disease_id INTEGER NOT NULL REFERENCES diseases(id) ON DELETE CASCADE,
    
    -- Tỉ lệ mắc bệnh
    probability DOUBLE PRECISION, -- Tỉ lệ/xác suất mắc bệnh (0.0000 - 1.0000)
    
    PRIMARY KEY (record_id, disease_id)
);

-- Tạo index cho bảng record_diseases
CREATE INDEX IF NOT EXISTS idx_record_diseases_disease ON record_diseases(disease_id);

-- Tạo bảng lịch sử train model
CREATE TABLE IF NOT EXISTS model_training_history (
    id SERIAL PRIMARY KEY,
    trigger_type VARCHAR(30), -- doctor_session_end, user_feedback
    triggered_by INTEGER REFERENCES users(id) ON DELETE SET NULL, -- User trigger training
    
    -- Dữ liệu training
    training_data_count INTEGER, -- Số lượng bản ghi dùng để train
    doctor_diagnosed_count INTEGER, -- Số bản ghi do bác sĩ chẩn đoán
    system_predicted_count INTEGER, -- Số bản ghi do hệ thống dự đoán
    
    deployed_at TIMESTAMP,
    
    -- Thời gian
    training_started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    training_completed_at TIMESTAMP,
    training_duration_seconds INTEGER,
    
    -- Status
    status VARCHAR(20) DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed', 'cancelled')),
    error_message TEXT,
    notes TEXT
);

-- Tạo index cho bảng model_training_history
CREATE INDEX IF NOT EXISTS idx_training_trigger ON model_training_history(trigger_type);
CREATE INDEX IF NOT EXISTS idx_training_user ON model_training_history(triggered_by);
CREATE INDEX IF NOT EXISTS idx_training_started ON model_training_history(training_started_at);
CREATE INDEX IF NOT EXISTS idx_training_status ON model_training_history(status);

-- Tạo bảng phiên làm việc của bác sĩ
CREATE TABLE IF NOT EXISTS doctor_sessions (
    id SERIAL PRIMARY KEY,
    doctor_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    
    -- Thống kê phiên làm việc
    total_records_created INTEGER DEFAULT 0,
    total_diagnoses_made INTEGER DEFAULT 0,
    total_patients_seen INTEGER DEFAULT 0,
    
    -- Trigger training
    auto_train_triggered BOOLEAN DEFAULT FALSE,
    training_id INTEGER REFERENCES model_training_history(id) ON DELETE SET NULL,
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'interrupted')),
    notes TEXT
);

-- Tạo index cho bảng doctor_sessions
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_doctor ON doctor_sessions(doctor_id);
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_start ON doctor_sessions(session_start);
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_end ON doctor_sessions(session_end);
CREATE INDEX IF NOT EXISTS idx_doctor_sessions_status ON doctor_sessions(status);

-- Insert dữ liệu mẫu cho bảng symptoms
INSERT INTO symptoms (name, code, description) VALUES
('Sốt', 'FEVER', 'Nhiệt độ cơ thể cao hơn bình thường'),
('Ho', 'COUGH', 'Phản xạ đẩy không khí ra khỏi phổi'),
('Đau đầu', 'HEADACHE', 'Cảm giác đau ở vùng đầu'),
('Đau họng', 'SORE_THROAT', 'Cảm giác đau, ngứa ở cổ họng'),
('Sổ mũi', 'RUNNY_NOSE', 'Tiết dịch mũi nhiều'),
('Mệt mỏi', 'FATIGUE', 'Cảm giác thiếu năng lượng'),
('Đau nhức cơ thể', 'BODY_ACHES', 'Đau nhức ở các cơ bắp'),
('Buồn nôn', 'NAUSEA', 'Cảm giác muốn nôn'),
('Tiêu chảy', 'DIARRHEA', 'Đi ngoài phân lỏng'),
('Khó thở', 'SHORTNESS_OF_BREATH', 'Cảm giác thiếu không khí')
ON CONFLICT (name) DO NOTHING;

-- Insert dữ liệu mẫu cho bảng diseases
INSERT INTO diseases (name, code, description, is_contagious) VALUES
('Cảm lạnh thông thường', 'COMMON_COLD', 'Nhiễm trùng đường hô hấp trên do virus', TRUE),
('Cúm mùa', 'SEASONAL_FLU', 'Nhiễm trùng do virus cúm', TRUE),
('Viêm dạ dày ruột', 'GASTROENTERITIS', 'Viêm dạ dày và ruột non', TRUE),
('Dị ứng thời tiết', 'ALLERGIC_RHINITIS', 'Phản ứng dị ứng với các chất trong không khí', FALSE),
('Sốc nhiệt', 'HEAT_EXHAUSTION', 'Tình trạng cơ thể quá nóng', FALSE),
('Khỏe mạnh', 'HEALTHY', 'Không có triệu chứng bệnh lý', FALSE),
('COVID-19', 'COVID19', 'Bệnh do virus SARS-CoV-2', TRUE),
('Viêm họng', 'PHARYNGITIS', 'Viêm niêm mạc họng', TRUE),
('Cao huyết áp', 'HYPERTENSION', 'Huyết áp cao', FALSE),
('Tiểu đường type 2', 'DIABETES_T2', 'Rối loạn chuyển hóa glucose', FALSE)
ON CONFLICT (name) DO NOTHING;

INSERT INTO users (username, email, password, first_name, last_name, date_of_birth, gender, phone, address, current_latitude, current_longitude, role, is_active)
VALUES
-- Patients
('patient01', 'patient01@example.com', 'hashed_pw_1', 'Linh', 'Nguyen', '1990-05-12', 'female', '0901234561', 'Hanoi', 21.0285, 105.8542, 'patient', TRUE),
('patient02', 'patient02@example.com', 'hashed_pw_2', 'Minh', 'Tran', '1985-09-20', 'male', '0901234562', 'Ho Chi Minh', 10.7626, 106.6602, 'patient', TRUE),
('patient03', 'patient03@example.com', 'hashed_pw_3', 'Anh', 'Le', '1993-12-03', 'female', '0901234563', 'Da Nang', 16.0544, 108.2022, 'patient', TRUE),
('patient04', 'patient04@example.com', 'hashed_pw_4', 'Hoang', 'Pham', '2000-03-15', 'male', '0901234564', 'Hue', 16.4637, 107.5909, 'patient', TRUE),
('patient05', 'patient05@example.com', 'hashed_pw_5', 'Thu', 'Do', '1998-08-25', 'female', '0901234565', 'Can Tho', 10.0452, 105.7469, 'patient', TRUE),
('patient06', 'patient06@example.com', 'hashed_pw_6', 'Tuan', 'Nguyen', '1991-11-30', 'male', '0901234566', 'Hai Phong', 20.8449, 106.6881, 'patient', TRUE),

-- Doctors
('doctor01', 'doctor01@example.com', 'hashed_pw_7', 'Khoa', 'Nguyen', '1978-04-10', 'male', '0901234567', 'Hanoi', NULL, NULL, 'doctor', TRUE),
('doctor02', 'doctor02@example.com', 'hashed_pw_8', 'Trang', 'Pham', '1982-07-18', 'female', '0901234568', 'Ho Chi Minh', NULL, NULL, 'doctor', TRUE),
('doctor03', 'doctor03@example.com', 'hashed_pw_9', 'Quang', 'Le', '1975-02-22', 'male', '0901234569', 'Da Nang', NULL, NULL, 'doctor', TRUE),
('doctor04', 'doctor04@example.com', 'hashed_pw_10', 'My', 'Tran', '1980-10-05', 'female', '0901234570', 'Hue', NULL, NULL, 'doctor', TRUE);

INSERT INTO medical_records (
    user_id, doctor_id, record_type, confidence_score, status, is_accurate,
    weather_temp, humidity, air_quality_index, season
)
SELECT
    -- Luân phiên user_id từ 1–6
    (i % 6) + 1 AS user_id,

    -- Luân phiên doctor_id từ 7–10
    7 + (i % 4) AS doctor_id,

    'doctor_diagnosis' AS record_type,
    NULL AS confidence_score,

    -- Xen kẽ status new / completed
    'completed' AS status,

    -- completed thì có is_accurate, ngẫu nhiên TRUE/FALSE
    CASE WHEN i % 2 = 0 THEN NULL ELSE (i % 3 = 0) END AS is_accurate,

    -- Weather, giả lập nhẹ
    ROUND((36.5 + random() * 3)::numeric, 1) AS weather_temp,
    FLOOR(50 + (random() * 30)) AS humidity,
    FLOOR(1 + (random() * 5)) AS air_quality_index,

    -- Luân phiên mùa
    CASE (i % 4)
        WHEN 0 THEN 'spring'
        WHEN 1 THEN 'summer'
        WHEN 2 THEN 'autumn'
        ELSE 'winter'
    END AS season

FROM generate_series(1, 100) AS s(i);

-- Grant permissions cho user database
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO health_predictor_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO health_predictor_user;
GRANT USAGE ON SCHEMA public TO health_predictor_user;

COMMENT ON TABLE users IS 'Bảng quản lý người dùng: bác sĩ, người bệnh, admin';
COMMENT ON TABLE symptoms IS 'Danh mục các triệu chứng có thể theo dõi';
COMMENT ON TABLE diseases IS 'Danh mục các loại bệnh với thông tin lây truyền';
COMMENT ON TABLE medical_records IS 'Lịch sử bệnh án - do bác sĩ hoặc hệ thống chuẩn đoán';
COMMENT ON TABLE record_symptoms IS 'Triệu chứng cụ thể trong từng bệnh án';
COMMENT ON TABLE record_diseases IS 'Bệnh được chẩn đoán trong từng bệnh án';
COMMENT ON TABLE model_training_history IS 'Lịch sử train model sau mỗi phiên bác sĩ hoặc theo lịch';
COMMENT ON TABLE doctor_sessions IS 'Phiên làm việc của bác sĩ - trigger train model khi kết thúc'; 